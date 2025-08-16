#!/usr/bin/env node

const { execSync } = require('child_process');
const fs = require('fs');

// Get all TypeScript/JavaScript files
function getAllFiles() {
  try {
    const command = `find . -type f \\( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \\) -not -path "./node_modules/*" -not -path "./.expo/*" -not -path "./dist/*"`;
    const output = execSync(command, { encoding: 'utf-8' });
    return output.trim().split('\n').filter(Boolean);
  } catch (error) {
    return [];
  }
}

// Check if a console statement is properly wrapped
function isConsoleProperlyWrapped(lines, lineIndex) {
  const line = lines[lineIndex].trim();

  // Skip if not a console statement
  if (!line.match(/console\.[a-zA-Z]/)) {
    return true;
  }

  // For console.error, it's OK if it has TODO comment
  if (line.includes('console.error') && line.includes('// TODO: Review for sensitive data')) {
    // Check if it's wrapped in __DEV__
    for (let i = lineIndex - 1; i >= Math.max(0, lineIndex - 5); i--) {
      if (lines[i].includes('if (__DEV__)')) {
        return true;
      }
    }
    return false;
  }

  // For other console methods, check for __DEV__ wrapper
  if (line.match(/console\.(log|info|debug|warn)/)) {
    for (let i = lineIndex - 1; i >= Math.max(0, lineIndex - 5); i--) {
      if (lines[i].includes('if (__DEV__)')) {
        return true;
      }
    }
    return false;
  }

  return true;
}

// Check a single file
function checkFile(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    const lines = content.split('\n');
    const unwrappedStatements = [];

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      if (line.match(/console\.[a-zA-Z]/) && !isConsoleProperlyWrapped(lines, i)) {
        unwrappedStatements.push({
          line: i + 1,
          content: line.trim(),
        });
      }
    }

    return unwrappedStatements;
  } catch (error) {
    return [];
  }
}

// Main execution
function main() {
  console.log('🔍 Final verification of console statement wrapping...\n');

  const files = getAllFiles();
  let totalUnwrapped = 0;
  let filesWithIssues = 0;

  const problemFiles = [];

  for (const file of files) {
    const unwrapped = checkFile(file);
    if (unwrapped.length > 0) {
      filesWithIssues++;
      totalUnwrapped += unwrapped.length;
      problemFiles.push({ file, statements: unwrapped });
    }
  }

  console.log(`📊 VERIFICATION RESULTS:`);
  console.log(`📁 Total files checked: ${files.length}`);
  console.log(`⚠️  Files with unwrapped console statements: ${filesWithIssues}`);
  console.log(`🚨 Total unwrapped console statements: ${totalUnwrapped}`);

  if (totalUnwrapped === 0) {
    console.log('\n✅ SUCCESS: All console statements are properly wrapped with __DEV__!');
  } else {
    console.log('\n❌ Issues found in the following files:');
    problemFiles.slice(0, 10).forEach(({ file, statements }) => {
      console.log(`\n📄 ${file}:`);
      statements.forEach(({ line, content }) => {
        console.log(`  Line ${line}: ${content}`);
      });
    });

    if (problemFiles.length > 10) {
      console.log(`\n... and ${problemFiles.length - 10} more files`);
    }
  }

  console.log('\n🎯 Issue #186 Status:');
  if (totalUnwrapped === 0) {
    console.log(
      '✅ COMPLETED: All console statements are now properly wrapped for production builds!',
    );
  } else {
    console.log(`⏳ IN PROGRESS: ${totalUnwrapped} console statements still need to be wrapped`);
  }
}

main();
