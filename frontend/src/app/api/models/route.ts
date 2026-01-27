import { NextResponse } from 'next/server';
import yaml from 'js-yaml';
import fs from 'fs';
import path from 'path';

export async function GET() {
  try {
    // Debug: Log current working directory
    const cwd = process.cwd();
    console.log(`[MODELS] Current working directory: ${cwd}`);

    // Try multiple paths for models.yaml
    const possiblePaths = [
      '/app/models.yaml', // Docker absolute path (most reliable - mounted from docker-compose)
      '/models.yaml', // Alternative absolute path
      path.join(cwd, 'models.yaml'), // From current working directory
      path.join(cwd, '..', 'models.yaml'), // From parent directory
      path.join(cwd, '..', '..', 'models.yaml'), // Alternative relative path
      path.join(__dirname, '..', '..', '..', '..', 'models.yaml'), // From route directory
    ];

    console.log(`[MODELS] Trying paths:`, possiblePaths);

    let modelsData: { models?: Array<{ id: string; label: string; input_cost: number; output_cost: number; default?: boolean }> } | undefined;
    let fileRead = false;

    for (const modelsPath of possiblePaths) {
      try {
        console.log(`[MODELS] Checking path: ${modelsPath}`);
        if (fs.existsSync(modelsPath)) {
          console.log(`[MODELS] File exists at: ${modelsPath}`);
          const fileContents = fs.readFileSync(modelsPath, 'utf8');
          modelsData = yaml.load(fileContents) as typeof modelsData;
          console.log(`[MODELS] Successfully loaded from: ${modelsPath}`);
          console.log(`[MODELS] Found ${modelsData?.models?.length || 0} models in file`);
          fileRead = true;
          break;
        } else {
          console.log(`[MODELS] File does not exist at: ${modelsPath}`);
        }
      } catch (err) {
        console.log(`[MODELS] Error reading from ${modelsPath}:`, err);
        continue;
      }
    }

    if (!fileRead) {
      console.warn('[MODELS] Could not read models.yaml, using fallback');
      console.warn('[MODELS] Please check if models.yaml is mounted correctly in docker-compose.yml');
      // Fallback to default models (including all current models)
      modelsData = {
        models: [
          {
            id: 'google/gemini-2.5-flash',
            label: 'Gemini 2.5 Flash',
            input_cost: 0.30,
            output_cost: 2.50,
          },
          {
            id: 'gpt-4o-mini',
            label: 'GPT-4o Mini',
            input_cost: 0.15,
            output_cost: 0.60,
          },
          {
            id: 'x-ai/grok-4-fast',
            label: 'Grok 4 Fast',
            input_cost: 0.20,
            output_cost: 0.50,
          },
          {
            id: 'x-ai/grok-4.1-fast:free',
            label: 'Grok 4.1 Fast (Free)',
            input_cost: 0.00,
            output_cost: 0.00,
            default: true,
          },
        ],
      };
    }

    console.log(`[MODELS] Returning ${modelsData?.models?.length || 0} models`);
    return NextResponse.json(modelsData || { models: [] });
  } catch (error) {
    console.error('[MODELS] Error loading models:', error);
    return NextResponse.json(
      { error: 'Failed to load models' },
      { status: 500 }
    );
  }
}

