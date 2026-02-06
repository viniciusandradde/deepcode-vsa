-- =============================================================================
-- 10_schema_fixes.sql - Fix schema issues from audit
-- Apply after all previous scripts
-- =============================================================================

-- 1. Add updated_at to planning_documents (was missing)
ALTER TABLE planning_documents
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Add trigger for auto-updating
DROP TRIGGER IF EXISTS trg_planning_documents_updated ON planning_documents;
CREATE TRIGGER trg_planning_documents_updated BEFORE
UPDATE ON planning_documents FOR EACH ROW EXECUTE FUNCTION update_planning_updated_at();

-- 2. CHECK constraints for status fields
DO $$ BEGIN
    -- planning_projects.status
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_planning_projects_status'
    ) THEN
        ALTER TABLE planning_projects
        ADD CONSTRAINT chk_planning_projects_status
        CHECK (status IN ('draft', 'active', 'completed', 'archived'));
    END IF;

    -- planning_stages.status
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_planning_stages_status'
    ) THEN
        ALTER TABLE planning_stages
        ADD CONSTRAINT chk_planning_stages_status
        CHECK (status IN ('pending', 'in_progress', 'completed'));
    END IF;

    -- planning_budget_items.category
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_planning_budget_category'
    ) THEN
        ALTER TABLE planning_budget_items
        ADD CONSTRAINT chk_planning_budget_category
        CHECK (category IN ('infra', 'pessoal', 'licencas', 'hardware', 'software', 'servicos', 'outros'));
    END IF;
END $$;
