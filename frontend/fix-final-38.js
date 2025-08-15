#!/usr/bin/env node

const fs = require('fs');

// List of files with unwrapped console statements from our verification
const filesToFix = [
  './components/tutorial/TutorialContext.tsx',
  './components/chat/ChatList.tsx', 
  './components/auth/SignUpWithDI.tsx',
  './components/auth/SignUp.old.tsx',
  './components/auth/SignInWithDI.tsx',
  './components/student/dashboard/AccountSettings.tsx',
  './components/modals/InviteTeacherModal.tsx',
  './components/communication/TemplateEditor.tsx',
  './hooks/useEmailAnalytics.ts',
  './services/websocket/auth/AsyncStorageAuthProvider.ts',
  './api/migration.ts',
  './scripts/migrate-button-to-v2.js'
];

function fixConsoleInFile(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    const lines = content.split('\n');
    let changes = 0;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const trimmedLine = line.trim();
      
      // Check if this line has a console statement and is not wrapped
      if (trimmedLine.match(/console\.(log|info|debug|warn|error)/) && !trimmedLine.includes('__DEV__')) {
        // Check if previous lines have __DEV__
        let isWrapped = false;
        for (let j = i - 1; j >= Math.max(0, i - 5); j--) {
          if (lines[j].includes('if (__DEV__)')) {
            isWrapped = true;
            break;
          }
        }
        
        if (!isWrapped) {
          // Get the indentation
          const indent = line.match(/^(\s*)/)[1];
          const statement = line.trim();
          
          // Replace this line and insert __DEV__ wrapper
          lines[i] = `${indent}if (__DEV__) {`;
          lines.splice(i + 1, 0, `${indent}  ${statement}`, `${indent}}`);
          changes++;
          i += 2; // Skip the lines we just added
        }
      }
    }
    
    if (changes > 0) {
      fs.writeFileSync(filePath, lines.join('\n'), 'utf-8');
      return changes;
    }
    
    return 0;
  } catch (error) {
    console.error(`Error processing ${filePath}:`, error.message);
    return 0;
  }
}

// Main execution
function main() {
  console.log('🚀 Fixing final 38 unwrapped console statements...\n');
  
  let totalChanges = 0;
  let filesProcessed = 0;
  
  for (const file of filesToFix) {
    try {
      const changes = fixConsoleInFile(file);
      if (changes > 0) {
        console.log(`✅ ${file}: ${changes} changes`);
        totalChanges += changes;
      }
      filesProcessed++;
    } catch (error) {
      console.error(`❌ Error processing ${file}:`, error.message);
    }
  }
  
  console.log(`\n📊 Summary:`);
  console.log(`📁 Files processed: ${filesProcessed}`);
  console.log(`🔧 Total changes: ${totalChanges}`);
  
  if (totalChanges > 0) {
    console.log('\n✨ Console statement wrapping complete!');
  } else {
    console.log('\n⚠️  No changes made - statements may already be wrapped');
  }
}

main();