#!/usr/bin/env node

/**
 * Migration script to update Button component imports from v1 to v2
 * This script will:
 * 1. Find all files importing the Button component
 * 2. Update the imports to use the v2 implementation
 * 3. Report any files that might need manual review
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Files to skip during migration
const SKIP_FILES = [
  'button-common.tsx',
  'button-v2.tsx',
  'button-v2.test.tsx',
  'button-migration-demo.tsx',
];

// Patterns to search and replace
const MIGRATION_PATTERNS = [
  {
    // Update imports from button/index to button/button-v2
    pattern: /from\s+['"]@\/components\/ui\/button['"]/g,
    replacement: 'from "@/components/ui/button/button-v2"',
  },
  {
    // Update relative imports
    pattern: /from\s+['"]\.\.\/button['"]/g,
    replacement: 'from "../button/button-v2"',
  },
  {
    pattern: /from\s+['"]\.\.\/\.\.\/button['"]/g,
    replacement: 'from "../../button/button-v2"',
  },
];

function findFilesWithButtonImports() {
  try {
    // Find all TypeScript/JavaScript files that import Button
    const command = `grep -r "from.*button" --include="*.tsx" --include="*.ts" --include="*.jsx" --include="*.js" . | grep -v node_modules | grep -v ".git" | cut -d: -f1 | sort | uniq`;
    const result = execSync(command, { encoding: 'utf-8', cwd: process.cwd() });
    return result.split('\n').filter(file => file.trim() !== '');
  } catch (error) {
    console.error('Error finding files:', error.message);
    return [];
  }
}

function shouldSkipFile(filePath) {
  const fileName = path.basename(filePath);
  return SKIP_FILES.includes(fileName) || filePath.includes('button-v2');
}

function migrateFile(filePath) {
  if (shouldSkipFile(filePath)) {
    console.log(`  ⏭️  Skipping: ${filePath}`);
    return { skipped: true };
  }

  try {
    let content = fs.readFileSync(filePath, 'utf-8');
    let modified = false;
    const originalContent = content;

    // Apply migration patterns
    MIGRATION_PATTERNS.forEach(({ pattern, replacement }) => {
      if (pattern.test(content)) {
        content = content.replace(pattern, replacement);
        modified = true;
      }
    });

    if (modified) {
      // Create backup
      const backupPath = `${filePath}.backup`;
      fs.writeFileSync(backupPath, originalContent);

      // Write migrated content
      fs.writeFileSync(filePath, content);

      console.log(`  ✅ Migrated: ${filePath}`);
      console.log(`     Backup created: ${backupPath}`);
      return { migrated: true, backup: backupPath };
    } else {
      console.log(`  ℹ️  No changes needed: ${filePath}`);
      return { unchanged: true };
    }
  } catch (error) {
    console.error(`  ❌ Error processing ${filePath}:`, error.message);
    return { error: true, message: error.message };
  }
}

function main() {
  console.log('🚀 Starting Button v1 to v2 migration...\n');

  const files = findFilesWithButtonImports();
  console.log(`Found ${files.length} files with button imports\n`);

  const results = {
    migrated: [],
    skipped: [],
    unchanged: [],
    errors: [],
  };

  files.forEach(file => {
    const result = migrateFile(file);
    if (result.migrated) {
      results.migrated.push(file);
    } else if (result.skipped) {
      results.skipped.push(file);
    } else if (result.unchanged) {
      results.unchanged.push(file);
    } else if (result.error) {
      results.errors.push({ file, error: result.message });
    }
  });

  // Print summary
  console.log('\n' + '='.repeat(50));
  console.log('📊 Migration Summary:\n');
  console.log(`✅ Migrated: ${results.migrated.length} files`);
  console.log(`⏭️  Skipped: ${results.skipped.length} files`);
  console.log(`ℹ️  Unchanged: ${results.unchanged.length} files`);
  console.log(`❌ Errors: ${results.errors.length} files`);

  if (results.errors.length > 0) {
    console.log('\n⚠️  Files with errors:');
    results.errors.forEach(({ file, error }) => {
      console.log(`  - ${file}: ${error}`);
    });
  }

  if (results.migrated.length > 0) {
    console.log('\n📝 Next steps:');
    console.log('1. Review the migrated files to ensure correctness');
    console.log('2. Run your tests to verify everything works');
    console.log('3. Delete backup files once confirmed: rm **/*.backup');
    console.log('4. Update button/index.tsx to export from button-v2.tsx');
    console.log('5. Remove @gluestack-ui/button from package.json');
  }

  console.log('\n✨ Migration script completed!');
}

// Check if we're in dry-run mode
const isDryRun = process.argv.includes('--dry-run');

if (isDryRun) {
  console.log('🔍 DRY RUN MODE - No files will be modified\n');
  const files = findFilesWithButtonImports();
  console.log(`Would process ${files.length} files:`);
  files.forEach(file => {
    if (!shouldSkipFile(file)) {
      console.log(`  - ${file}`);
    }
  });
} else {
  main();
}
