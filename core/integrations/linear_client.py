"""Linear.app GraphQL API Client.

Reference: https://developers.linear.app/docs/graphql/working-with-the-graphql-api

All mutations use GraphQL variables to prevent injection attacks.
"""

import httpx
from typing import Any, Optional, List

from .tool_result import ToolResult


class LinearClient:
    """Linear.app GraphQL API client.

    Implements issue management, project tracking, and team operations.
    Uses GraphQL with parameterized variables for all API calls.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.linear.app/graphql"
        self._client: httpx.AsyncClient | None = None

    @property
    def headers(self) -> dict:
        """Get request headers."""
        return {
            "Content-Type": "application/json",
            "Authorization": self.api_key,
        }

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def _graphql_query(self, query: str, variables: dict | None = None) -> ToolResult:
        """Execute a GraphQL query."""
        client = await self._get_client()

        payload = {
            "query": query,
            "variables": variables or {}
        }

        try:
            response = await client.post(
                self.api_url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                return ToolResult.fail(
                    f"GraphQL Error: {data['errors']}",
                    operation="graphql_query"
                )

            return ToolResult.ok(data.get("data", {}), operation="graphql_query")

        except httpx.HTTPStatusError as e:
            detail = ""
            try:
                body = e.response.json() if e.response.headers.get("content-type", "").startswith("application/json") else {}
                detail = body.get("errors", body.get("message", e.response.text or ""))
                if isinstance(detail, list):
                    detail = "; ".join(str(x) for x in detail[:3])
            except Exception:
                detail = e.response.text[:200] if e.response.text else ""
            msg = f"HTTP Error: {e.response.status_code}"
            if detail:
                msg += f" — {detail}"
            if e.response.status_code == 401:
                msg += " (verifique LINEAR_API_KEY em .env e em https://linear.app/settings/api)"
            return ToolResult.fail(msg, operation="graphql_query")
        except Exception as e:
            return ToolResult.fail(str(e), operation="graphql_query")

    async def get_issues(
        self,
        team_id: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 10,
        assignee_id: Optional[str] = None,
    ) -> ToolResult:
        """Get issues from Linear."""
        filter_parts = []
        variables: dict[str, Any] = {}

        if team_id:
            filter_parts.append('team: { id: { eq: $teamId } }')
            variables["teamId"] = team_id
        if state:
            filter_parts.append('state: { name: { eq: $stateName } }')
            variables["stateName"] = state
        if assignee_id:
            filter_parts.append('assignee: { id: { eq: $assigneeId } }')
            variables["assigneeId"] = assignee_id

        # Build variable declarations for the query
        var_decls = []
        if team_id:
            var_decls.append("$teamId: String!")
        if state:
            var_decls.append("$stateName: String!")
        if assignee_id:
            var_decls.append("$assigneeId: String!")

        filter_str = ", ".join(filter_parts) if filter_parts else ""
        var_decl_str = f"({', '.join(var_decls)})" if var_decls else ""

        query = f"""
        query {var_decl_str} {{
          issues(
            first: {limit}
            {f'filter: {{ {filter_str} }}' if filter_str else ''}
            orderBy: updatedAt
          ) {{
            nodes {{
              id
              identifier
              title
              description
              priority
              priorityLabel
              state {{
                name
                type
              }}
              assignee {{
                id
                name
                email
              }}
              team {{
                id
                name
              }}
              createdAt
              updatedAt
              url
            }}
          }}
        }}
        """

        result = await self._graphql_query(query, variables if variables else None)

        if not result.success:
            return result

        issues = result.output.get("issues", {}).get("nodes", [])

        return ToolResult.ok(
            {
                "issues": issues,
                "count": len(issues)
            },
            operation="get_issues"
        )

    async def get_issue(self, issue_id: str) -> ToolResult:
        """Get single issue details by ID or identifier (e.g., 'ENG-123')."""
        query = """
        query($issueId: String!) {
          issue(id: $issueId) {
            id
            identifier
            title
            description
            priority
            priorityLabel
            state {
              name
              type
            }
            assignee {
              id
              name
              email
            }
            team {
              id
              name
              key
            }
            labels {
              nodes {
                id
                name
              }
            }
            comments {
              nodes {
                id
                body
                user {
                  name
                }
                createdAt
              }
            }
            createdAt
            updatedAt
            url
          }
        }
        """

        result = await self._graphql_query(query, {"issueId": issue_id})

        if not result.success:
            return result

        issue = result.output.get("issue")

        if not issue:
            return ToolResult.fail(
                f"Issue {issue_id} not found",
                operation="get_issue"
            )

        return ToolResult.ok(
            {"issue": issue},
            operation="get_issue"
        )

    async def create_issue(
        self,
        team_id: str,
        title: str,
        description: str,
        priority: int = 3,
        state_id: Optional[str] = None,
        assignee_id: Optional[str] = None,
        label_ids: Optional[List[str]] = None,
        dry_run: bool = True
    ) -> ToolResult:
        """Create a new issue in Linear using GraphQL variables."""
        if dry_run:
            return ToolResult.ok(
                {
                    "preview": {
                        "team_id": team_id,
                        "title": title,
                        "description": description,
                        "priority": priority,
                        "state_id": state_id,
                        "assignee_id": assignee_id,
                        "label_ids": label_ids,
                    },
                    "dry_run": True,
                    "message": "Issue would be created with these values"
                },
                operation="create_issue"
            )

        variables: dict[str, Any] = {
            "teamId": team_id,
            "title": title,
            "description": description,
            "priority": priority,
        }
        if state_id:
            variables["stateId"] = state_id
        if assignee_id:
            variables["assigneeId"] = assignee_id
        if label_ids:
            variables["labelIds"] = label_ids

        # Build variable declarations
        var_decls = [
            "$teamId: String!",
            "$title: String!",
            "$description: String!",
            "$priority: Int!",
        ]
        input_fields = [
            "teamId: $teamId",
            "title: $title",
            "description: $description",
            "priority: $priority",
        ]
        if state_id:
            var_decls.append("$stateId: String!")
            input_fields.append("stateId: $stateId")
        if assignee_id:
            var_decls.append("$assigneeId: String!")
            input_fields.append("assigneeId: $assigneeId")
        if label_ids:
            var_decls.append("$labelIds: [String!]!")
            input_fields.append("labelIds: $labelIds")

        mutation = f"""
        mutation({', '.join(var_decls)}) {{
          issueCreate(input: {{ {', '.join(input_fields)} }}) {{
            success
            issue {{
              id
              identifier
              title
              url
            }}
          }}
        }}
        """

        result = await self._graphql_query(mutation, variables)

        if not result.success:
            return result

        create_result = result.output.get("issueCreate", {})

        if not create_result.get("success"):
            return ToolResult.fail(
                "Failed to create issue",
                operation="create_issue"
            )

        issue = create_result.get("issue", {})

        return ToolResult.ok(
            {
                "issue_id": issue.get("id"),
                "identifier": issue.get("identifier"),
                "url": issue.get("url"),
                "created": True
            },
            operation="create_issue"
        )

    async def get_teams(self) -> ToolResult:
        """Get all teams in the organization."""
        query = """
        query {
          teams {
            nodes {
              id
              name
              key
              description
            }
          }
        }
        """

        result = await self._graphql_query(query)

        if not result.success:
            return result

        teams = result.output.get("teams", {}).get("nodes", [])

        return ToolResult.ok(
            {"teams": teams, "count": len(teams)},
            operation="get_teams"
        )

    async def get_workflow_states(self, team_id: str) -> ToolResult:
        """Get workflow states for a team."""
        query = """
        query($teamId: String!) {
          team(id: $teamId) {
            states {
              nodes {
                id
                name
                type
                color
                description
              }
            }
          }
        }
        """

        result = await self._graphql_query(query, {"teamId": team_id})

        if not result.success:
            return result

        states = result.output.get("team", {}).get("states", {}).get("nodes", [])

        return ToolResult.ok(
            {"states": states, "count": len(states)},
            operation="get_workflow_states"
        )

    async def add_comment(
        self,
        issue_id: str,
        body: str,
        dry_run: bool = True
    ) -> ToolResult:
        """Add a comment to an issue using GraphQL variables."""
        if dry_run:
            return ToolResult.ok(
                {
                    "preview": {
                        "issue_id": issue_id,
                        "body": body,
                    },
                    "dry_run": True,
                    "message": "Comment would be added"
                },
                operation="add_comment"
            )

        mutation = """
        mutation($issueId: String!, $body: String!) {
          commentCreate(input: {
            issueId: $issueId
            body: $body
          }) {
            success
            comment {
              id
              body
              createdAt
            }
          }
        }
        """

        result = await self._graphql_query(mutation, {"issueId": issue_id, "body": body})

        if not result.success:
            return result

        create_result = result.output.get("commentCreate", {})

        if not create_result.get("success"):
            return ToolResult.fail(
                "Failed to create comment",
                operation="add_comment"
            )

        return ToolResult.ok(
            {
                "comment_id": create_result.get("comment", {}).get("id"),
                "created": True
            },
            operation="add_comment"
        )

    async def create_project(
        self,
        team_id: str,
        name: str,
        description: str = "",
        summary: str = "",
        start_date: Optional[str] = None,
        target_date: Optional[str] = None,
        priority: int = 0,
        dry_run: bool = True
    ) -> ToolResult:
        """Create a project in Linear using GraphQL variables."""
        if dry_run:
            return ToolResult.ok(
                {
                    "preview": {
                        "team_id": team_id,
                        "name": name,
                        "description": description,
                        "summary": summary[:255] if summary else "",
                        "start_date": start_date,
                        "target_date": target_date,
                        "priority": priority,
                    },
                    "dry_run": True,
                    "message": "Project would be created with these values",
                },
                operation="create_project"
            )

        variables: dict[str, Any] = {
            "teamIds": [team_id],
            "name": name,
        }
        var_decls = [
            "$teamIds: [String!]!",
            "$name: String!",
        ]
        input_fields = [
            "teamIds: $teamIds",
            "name: $name",
        ]

        if description:
            variables["description"] = description
            var_decls.append("$description: String")
            input_fields.append("description: $description")
        if summary:
            variables["summary"] = summary[:255]
            var_decls.append("$summary: String")
            input_fields.append("summary: $summary")
        if start_date:
            variables["startDate"] = start_date
            var_decls.append("$startDate: TimelessDate")
            input_fields.append("startDate: $startDate")
        if target_date:
            variables["targetDate"] = target_date
            var_decls.append("$targetDate: TimelessDate")
            input_fields.append("targetDate: $targetDate")
        if priority is not None and priority >= 0:
            variables["priority"] = priority
            var_decls.append("$priority: Int")
            input_fields.append("priority: $priority")

        mutation = f"""
        mutation({', '.join(var_decls)}) {{
          projectCreate(input: {{ {', '.join(input_fields)} }}) {{
            success
            project {{
              id
              name
              url
              state
            }}
          }}
        }}
        """
        result = await self._graphql_query(mutation, variables)
        if not result.success:
            return result

        create_result = result.output.get("projectCreate", {})
        if not create_result.get("success"):
            return ToolResult.fail("Failed to create project", operation="create_project")

        project = create_result.get("project", {})
        return ToolResult.ok(
            {
                "project_id": project.get("id"),
                "name": project.get("name"),
                "url": project.get("url"),
                "created": True,
            },
            operation="create_project"
        )

    async def create_project_milestone(
        self,
        project_id: str,
        name: str,
        target_date: Optional[str] = None,
        description: str = "",
        dry_run: bool = True
    ) -> ToolResult:
        """Create a milestone in a Linear project using GraphQL variables."""
        if dry_run:
            return ToolResult.ok(
                {
                    "preview": {
                        "project_id": project_id,
                        "name": name,
                        "target_date": target_date,
                        "description": description,
                    },
                    "dry_run": True,
                    "message": "Milestone would be created",
                },
                operation="create_project_milestone"
            )

        variables: dict[str, Any] = {
            "projectId": project_id,
            "name": name,
        }
        var_decls = ["$projectId: String!", "$name: String!"]
        input_fields = ["projectId: $projectId", "name: $name"]

        if target_date:
            variables["targetDate"] = target_date
            var_decls.append("$targetDate: TimelessDate")
            input_fields.append("targetDate: $targetDate")
        if description:
            variables["description"] = description
            var_decls.append("$description: String")
            input_fields.append("description: $description")

        mutation = f"""
        mutation({', '.join(var_decls)}) {{
          projectMilestoneCreate(input: {{ {', '.join(input_fields)} }}) {{
            success
            projectMilestone {{
              id
              name
              targetDate
            }}
          }}
        }}
        """
        result = await self._graphql_query(mutation, variables)
        if not result.success:
            return result

        create_result = result.output.get("projectMilestoneCreate", {})
        if not create_result.get("success"):
            return ToolResult.fail(
                "Failed to create project milestone",
                operation="create_project_milestone"
            )

        milestone = create_result.get("projectMilestone", {})
        return ToolResult.ok(
            {
                "milestone_id": milestone.get("id"),
                "name": milestone.get("name"),
                "target_date": milestone.get("targetDate"),
                "created": True,
            },
            operation="create_project_milestone"
        )

    async def create_project_with_plan(
        self,
        team_id: str,
        plan: dict,
        dry_run: bool = True
    ) -> ToolResult:
        """Create project with milestones and tasks (issues)."""
        proj = (plan.get("project") or {}).copy()
        milestones = plan.get("milestones") or []
        tasks = plan.get("tasks") or []

        MAX_TASKS = 50
        if len(tasks) > MAX_TASKS:
            return ToolResult.fail(
                f"Too many tasks (max {MAX_TASKS})",
                operation="create_project_with_plan"
            )

        if dry_run:
            return ToolResult.ok(
                {
                    "preview": {
                        "project": proj,
                        "milestones": milestones,
                        "tasks": tasks,
                        "team_id": team_id,
                    },
                    "dry_run": True,
                    "message": "Project plan preview; confirm to create in Linear",
                },
                operation="create_project_with_plan"
            )

        # 1. Create project
        res = await self.create_project(
            team_id=team_id,
            name=proj.get("name") or "Novo Projeto",
            description=proj.get("description") or "",
            summary=proj.get("summary") or "",
            start_date=proj.get("startDate") or None,
            target_date=proj.get("targetDate") or None,
            priority=proj.get("priority", 0),
            dry_run=False
        )
        if not res.success:
            return res
        project_id = res.output.get("project_id")
        if not project_id:
            return ToolResult.fail("Project created but no project_id returned", operation="create_project_with_plan")

        # 2. Create milestones and map name -> id
        milestone_name_to_id: dict[str, str] = {}
        for m in milestones:
            m_name = m.get("name") or ""
            m_res = await self.create_project_milestone(
                project_id=project_id,
                name=m_name,
                target_date=m.get("targetDate") or None,
                description=m.get("description") or "",
                dry_run=False
            )
            if not m_res.success:
                return ToolResult.fail(
                    f"Failed to create milestone '{m_name}': {m_res.error}",
                    operation="create_project_with_plan"
                )
            mid = m_res.output.get("milestone_id")
            if mid:
                milestone_name_to_id[m_name] = mid

        # 3. Create issues (tasks) and link to project
        created_issues = []
        for t in tasks:
            title = t.get("title") or "Tarefa"
            issue_res = await self.create_issue(
                team_id=team_id,
                title=title,
                description=t.get("description") or "",
                priority=t.get("priority", 3),
                dry_run=False
            )
            if not issue_res.success:
                return ToolResult.fail(
                    f"Failed to create issue '{title}': {issue_res.error}",
                    operation="create_project_with_plan"
                )
            issue_id = issue_res.output.get("issue_id")
            if not issue_id:
                continue
            created_issues.append({
                "title": title,
                "issue_id": issue_id,
                "identifier": issue_res.output.get("identifier"),
            })

            # Link issue to project using GraphQL variables
            t_milestone_name = t.get("milestone")
            variables: dict[str, Any] = {
                "issueId": issue_id,
                "projectId": project_id,
            }
            var_decls = ["$issueId: String!", "$projectId: String!"]
            input_fields = ["id: $issueId", "projectId: $projectId"]

            if t_milestone_name and milestone_name_to_id.get(t_milestone_name):
                variables["milestoneId"] = milestone_name_to_id[t_milestone_name]
                var_decls.append("$milestoneId: String!")
                input_fields.append("projectMilestoneId: $milestoneId")

            update_mutation = f"""
            mutation({', '.join(var_decls)}) {{
              issueUpdate(input: {{ {', '.join(input_fields)} }}) {{
                success
                issue {{ id identifier }}
              }}
            }}
            """
            await self._graphql_query(update_mutation, variables)

        return ToolResult.ok(
            {
                "project_id": project_id,
                "project_url": res.output.get("url") or "",
                "milestones_created": len(milestone_name_to_id),
                "issues_created": created_issues,
                "created": True,
            },
            operation="create_project_with_plan"
        )

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
