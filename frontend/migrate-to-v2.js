#!/usr/bin/env node

/**
 * Migration Script: Gluestack UI v1 to v2
 *
 * This script:
 * 1. Creates backups of all component index files
 * 2. Updates main component index.tsx files to export from v2
 * 3. Provides rollback functionality
 *
 * Usage:
 *   node migrate-to-v2.js backup    - Create backups
 *   node migrate-to-v2.js migrate   - Run migration
 *   node migrate-to-v2.js rollback  - Rollback changes
 *   node migrate-to-v2.js test      - Test critical imports
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Components that have v2 versions
const COMPONENTS_WITH_V2 = [
  'accordion',
  'alert',
  'avatar',
  'button',
  'card',
  'checkbox',
  'divider',
  'fab',
  'form-control',
  'icon',
  'image',
  'input',
  'link',
  'menu',
  'modal',
  'pressable',
  'progress',
  'radio',
  'select',
  'slider',
  'spinner',
  'switch',
  'textarea',
  'toast',
];

const COMPONENTS_DIR = './components/ui';
const BACKUP_DIR = './migration-backups';

function createBackups() {
  console.log('🔄 Creating backups...');

  // Create backup directory
  if (!fs.existsSync(BACKUP_DIR)) {
    fs.mkdirSync(BACKUP_DIR, { recursive: true });
  }

  for (const component of COMPONENTS_WITH_V2) {
    const indexPath = path.join(COMPONENTS_DIR, component, 'index.tsx');
    const backupPath = path.join(BACKUP_DIR, `${component}-index.tsx`);

    if (fs.existsSync(indexPath)) {
      fs.copyFileSync(indexPath, backupPath);
      console.log(`✅ Backed up: ${component}/index.tsx`);
    }
  }

  // Also backup package.json
  fs.copyFileSync('./package.json', path.join(BACKUP_DIR, 'package.json'));
  console.log('✅ Backed up: package.json');
}

function migrateComponents() {
  console.log('🚀 Starting migration...');

  for (const component of COMPONENTS_WITH_V2) {
    const indexPath = path.join(COMPONENTS_DIR, component, 'index.tsx');
    const v2Path = path.join(COMPONENTS_DIR, component, `${component}-v2.tsx`);

    // Check if v2 file exists
    if (!fs.existsSync(v2Path)) {
      console.log(`⚠️  Skipping ${component}: v2 file not found`);
      continue;
    }

    // Create new index.tsx that exports from v2
    const newIndexContent = `// Auto-migrated to use v2 components
export * from './${component}-v2';
`;

    fs.writeFileSync(indexPath, newIndexContent);
    console.log(`✅ Migrated: ${component}/index.tsx -> ${component}-v2.tsx`);
  }
}

function rollbackComponents() {
  console.log('🔄 Rolling back migration...');

  for (const component of COMPONENTS_WITH_V2) {
    const indexPath = path.join(COMPONENTS_DIR, component, 'index.tsx');
    const backupPath = path.join(BACKUP_DIR, `${component}-index.tsx`);

    if (fs.existsSync(backupPath)) {
      fs.copyFileSync(backupPath, indexPath);
      console.log(`✅ Restored: ${component}/index.tsx`);
    }
  }

  // Restore package.json
  const packageBackupPath = path.join(BACKUP_DIR, 'package.json');
  if (fs.existsSync(packageBackupPath)) {
    fs.copyFileSync(packageBackupPath, './package.json');
    console.log('✅ Restored: package.json');
  }
}

function testCriticalImports() {
  console.log('🧪 Testing critical imports...');

  const testFiles = [
    './app/sign-in.tsx',
    './app/sign-up.tsx',
    './app/(tabs)/index.tsx',
    './components/auth/SignIn.tsx',
    './components/auth/SignUp.tsx',
  ];

  for (const testFile of testFiles) {
    if (fs.existsSync(testFile)) {
      try {
        // Try to compile the file with TypeScript
        execSync(`npx tsc --noEmit --skipLibCheck ${testFile}`, { stdio: 'pipe' });
        console.log(`✅ ${testFile}: Compiles successfully`);
      } catch (error) {
        console.log(`❌ ${testFile}: Compilation failed`);
        console.log(error.stdout?.toString() || error.message);
      }
    } else {
      console.log(`⚠️  ${testFile}: File not found`);
    }
  }
}

function removeOldPackages() {
  console.log('🧹 Removing old Gluestack v1 packages...');

  const packagesToRemove = [
    '@gluestack-ui/accordion',
    '@gluestack-ui/actionsheet',
    '@gluestack-ui/alert',
    '@gluestack-ui/alert-dialog',
    '@gluestack-ui/avatar',
    '@gluestack-ui/button',
    '@gluestack-ui/checkbox',
    '@gluestack-ui/divider',
    '@gluestack-ui/fab',
    '@gluestack-ui/form-control',
    '@gluestack-ui/icon',
    '@gluestack-ui/image',
    '@gluestack-ui/input',
    '@gluestack-ui/link',
    '@gluestack-ui/menu',
    '@gluestack-ui/modal',
    '@gluestack-ui/overlay',
    '@gluestack-ui/popover',
    '@gluestack-ui/pressable',
    '@gluestack-ui/progress',
    '@gluestack-ui/radio',
    '@gluestack-ui/select',
    '@gluestack-ui/slider',
    '@gluestack-ui/spinner',
    '@gluestack-ui/switch',
    '@gluestack-ui/textarea',
    '@gluestack-ui/toast',
    '@gluestack-ui/tooltip',
  ];

  try {
    const packageJson = JSON.parse(fs.readFileSync('./package.json', 'utf8'));
    let removed = 0;

    packagesToRemove.forEach(pkg => {
      if (packageJson.dependencies && packageJson.dependencies[pkg]) {
        delete packageJson.dependencies[pkg];
        removed++;
        console.log(`✅ Removed: ${pkg}`);
      }
      if (packageJson.devDependencies && packageJson.devDependencies[pkg]) {
        delete packageJson.devDependencies[pkg];
        removed++;
        console.log(`✅ Removed: ${pkg} (dev)`);
      }
    });

    fs.writeFileSync('./package.json', JSON.stringify(packageJson, null, 2) + '\n');
    console.log(`🎉 Removed ${removed} old packages from package.json`);
    console.log('💡 Run "npm install" to clean up node_modules');
  } catch (error) {
    console.error('❌ Error updating package.json:', error.message);
  }
}

// Main execution
const command = process.argv[2];

switch (command) {
  case 'backup':
    createBackups();
    break;

  case 'migrate':
    migrateComponents();
    break;

  case 'rollback':
    rollbackComponents();
    break;

  case 'test':
    testCriticalImports();
    break;

  case 'remove-packages':
    removeOldPackages();
    break;

  case 'full-migration':
    createBackups();
    console.log('');
    migrateComponents();
    console.log('');
    testCriticalImports();
    console.log('');
    console.log(
      '🎉 Migration complete! Run "node migrate-to-v2.js remove-packages" when ready to clean up old packages.'
    );
    break;

  default:
    console.log(`
🚀 Gluestack UI v1 to v2 Migration Tool

Usage:
  node migrate-to-v2.js backup           - Create backups of index files
  node migrate-to-v2.js migrate          - Update components to use v2
  node migrate-to-v2.js test             - Test critical file imports
  node migrate-to-v2.js remove-packages  - Remove old v1 packages
  node migrate-to-v2.js rollback         - Restore from backups
  node migrate-to-v2.js full-migration   - Run complete migration

Components with v2 versions: ${COMPONENTS_WITH_V2.length}
${COMPONENTS_WITH_V2.map(c => `  • ${c}`).join('\n')}
`);
    break;
}
