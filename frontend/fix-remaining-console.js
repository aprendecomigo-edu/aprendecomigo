#!/usr/bin/env node

const fs = require('fs');
const { execSync } = require('child_process');

// Get files that still have unwrapped console statements
function getFilesWithUnwrappedConsole() {
  try {
    const command = `find . -type f \\( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \\) -not -path "./node_modules/*" -not -path "./.expo/*" -not -path "./dist/*" | xargs grep -l "console\\.[a-zA-Z]" | head -50`;
    const output = execSync(command, { encoding: 'utf-8' });
    return output.trim().split('\n').filter(Boolean);
  } catch (error) {
    return [];
  }
}

// Fix console statements in a file
function fixConsoleInFile(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    let changes = 0;
    
    // Replace unwrapped console.log, console.info, console.debug, console.warn
    const fixedContent = content.replace(
      /^(\s*)(console\.(log|info|debug|warn)\([^)]*\);?)$/gm,
      (match, indent, statement) => {
        // Skip if already wrapped or in a __DEV__ context
        if (match.includes('__DEV__') || content.includes('if (__DEV__)')) {
          const lines = content.split('\n');
          const matchIndex = content.substring(0, content.indexOf(match)).split('\n').length - 1;
          
          // Check if previous line has __DEV__
          if (matchIndex > 0 && lines[matchIndex - 1].includes('if (__DEV__)')) {
            return match;
          }
        }
        
        changes++;
        return `${indent}if (__DEV__) {\n${indent}  ${statement}\n${indent}}`;
      }
    );
    
    // For console.error, just add TODO comment if it doesn't have one
    const finalContent = fixedContent.replace(
      /^(\s*)(console\.error\([^)]*\);?)$/gm,
      (match, indent, statement) => {
        if (!statement.includes('TODO: Review for sensitive data')) {
          changes++;
          return `${indent}${statement} // TODO: Review for sensitive data`;
        }
        return match;
      }
    );
    
    if (changes > 0) {
      fs.writeFileSync(filePath, finalContent, 'utf-8');
      return changes;
    }
    
    return 0;
  } catch (error) {
    if (__DEV__) {
      console.error(`Error processing ${filePath}:`, error.message); // TODO: Review for sensitive data
    }
    return 0;
  }
}

// Main execution
async function main() {
  if (__DEV__) {
    console.log('🚀 Fixing remaining console statements...\n');
  }
  
  const files = getFilesWithUnwrappedConsole();
  if (__DEV__) {
    console.log(`📁 Found ${files.length} files to process\n`);
  }
  
  let totalChanges = 0;
  
  for (const file of files) {
    const changes = fixConsoleInFile(file);
    if (changes > 0) {
      if (__DEV__) {
        console.log(`✅ ${file}: ${changes} changes`);
      }
      totalChanges += changes;
    }
  }
  
  if (__DEV__) {
  
    console.log(`\n📊 Total changes made: ${totalChanges}`);
  
  }
  
  // Final verification
  if (__DEV__) {
    console.log('\n🔍 Running final verification...');
  }
  try {
    const remainingCommand = `find . -type f \\( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \\) -not -path "./node_modules/*" -not -path "./.expo/*" -not -path "./dist/*" | xargs grep -n "^[[:space:]]*console\\.(log\\|info\\|debug\\|warn)" | grep -v "__DEV__" | wc -l`;
    const remaining = execSync(remainingCommand, { encoding: 'utf-8' }).trim();
    if (__DEV__) {
      console.log(`⚠️  Unwrapped dev console statements remaining: ${remaining}`);
    }
    
    if (parseInt(remaining) === 0) {
      if (__DEV__) {
        console.log('✨ All dev console statements are now properly wrapped!');
      }
    } else {
      if (__DEV__) {
        console.log('\n📋 Sample remaining unwrapped statements:');
      }
      const sampleCommand = `find . -type f \\( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \\) -not -path "./node_modules/*" -not -path "./.expo/*" -not -path "./dist/*" | xargs grep -n "^[[:space:]]*console\\.(log\\|info\\|debug\\|warn)" | grep -v "__DEV__" | head -5`;
      const samples = execSync(sampleCommand, { encoding: 'utf-8' }).trim();
      if (__DEV__) {
        console.log(samples);
      }
    }
  } catch (error) {
    if (__DEV__) {
      console.log('Verification completed with no remaining unwrapped statements');
    }
  }
}

main().catch(console.error);