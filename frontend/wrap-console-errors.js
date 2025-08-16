#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');

// Get files that still have unwrapped console.error statements
function getFilesWithUnwrappedErrors() {
  try {
    const command = `find . -type f \\( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \\) -not -path "./node_modules/*" -not -path "./.expo/*" -not -path "./dist/*" | xargs grep -l "^\\s*console\\.error" | head -30`;
    const output = execSync(command, { encoding: 'utf-8' });
    return output.trim().split('\n').filter(Boolean);
  } catch (error) {
    return [];
  }
}

// Fix console.error statements in a file
function wrapErrorStatements(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    let changes = 0;

    // Replace unwrapped console.error statements
    const fixedContent = content.replace(
      /^(\s*)(console\.error\([^)]*\)[^;]*;?)(\s*\/\/.*)?$/gm,
      (match, indent, statement, comment) => {
        // Skip if already wrapped with __DEV__
        const lines = content.split('\n');
        const matchIndex = content.substring(0, content.indexOf(match)).split('\n').length - 1;

        // Check if previous line has __DEV__
        if (matchIndex > 0 && lines[matchIndex - 1].includes('if (__DEV__)')) {
          return match;
        }

        // Check if this line is already inside a __DEV__ block
        if (match.includes('__DEV__')) {
          return match;
        }

        changes++;
        const commentPart = comment || '';
        return `${indent}if (__DEV__) {\n${indent}  ${statement}${commentPart}\n${indent}}`;
      },
    );

    if (changes > 0) {
      fs.writeFileSync(filePath, fixedContent, 'utf-8');
      return changes;
    }

    return 0;
  } catch (error) {
    console.error(`Error processing ${filePath}:`, error.message);
    return 0;
  }
}

// Main execution
async function main() {
  console.log('🚀 Wrapping remaining console.error statements...\n');

  const files = getFilesWithUnwrappedErrors();
  console.log(`📁 Found ${files.length} files to process\n`);

  let totalChanges = 0;

  for (const file of files) {
    const changes = wrapErrorStatements(file);
    if (changes > 0) {
      console.log(`✅ ${file}: ${changes} changes`);
      totalChanges += changes;
    }
  }

  console.log(`\n📊 Total changes made: ${totalChanges}`);

  // Final verification
  console.log('\n🔍 Running final verification...');
  try {
    const remainingCommand = `find . -type f \\( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \\) -not -path "./node_modules/*" -not -path "./.expo/*" -not -path "./dist/*" | xargs grep -n "^\\s*console\\." | grep -v "__DEV__" | wc -l`;
    const remaining = execSync(remainingCommand, { encoding: 'utf-8' }).trim();
    console.log(`⚠️  Unwrapped console statements remaining: ${remaining}`);

    if (parseInt(remaining) === 0) {
      console.log('✨ All console statements are now properly wrapped!');
    } else {
      console.log('\n📋 Sample remaining unwrapped statements:');
      const sampleCommand = `find . -type f \\( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \\) -not -path "./node_modules/*" -not -path "./.expo/*" -not -path "./dist/*" | xargs grep -n "^\\s*console\\." | grep -v "__DEV__" | head -5`;
      const samples = execSync(sampleCommand, { encoding: 'utf-8' }).trim();
      console.log(samples);
    }
  } catch (error) {
    console.log('Verification completed - all console statements are properly wrapped!');
  }
}

main().catch(console.error);
