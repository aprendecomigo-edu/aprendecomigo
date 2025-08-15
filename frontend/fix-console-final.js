#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class ConsoleStatementFixerFinal {
  constructor() {
    this.processedFiles = 0;
    this.totalChanges = 0;
    this.errors = [];
    this.results = {
      wrapped: 0,
      sanitized: 0,
      skipped: 0
    };
  }

  // Find all TypeScript/JavaScript files with actual console statements
  findFilesWithConsole() {
    try {
      const command = `find . -type f \\( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \\) -not -path "./node_modules/*" -not -path "./.expo/*" -not -path "./dist/*" | xargs grep -l "console\\.[a-zA-Z]" | grep -v "__DEV__"`;
      const output = execSync(command, { encoding: 'utf-8' });
      return output.trim().split('\n').filter(Boolean);
    } catch (error) {
      // If no files found, return empty array
      return [];
    }
  }

  // Process a single file with comprehensive console statement handling
  processFile(filePath) {
    try {
      const originalContent = fs.readFileSync(filePath, 'utf-8');
      let content = originalContent;
      let fileChanges = 0;

      // Replace console statements that are NOT already wrapped with __DEV__
      content = content.replace(
        /(^.*?)(\s*)(console\.(log|info|debug|warn|error).*?;?)$/gm,
        (match, prefix, indent, consoleStatement, method) => {
          // Skip if already wrapped (check previous lines)
          const lines = content.split('\n');
          const matchIndex = content.substring(0, content.indexOf(match)).split('\n').length - 1;
          
          // Check if previous line contains __DEV__
          if (matchIndex > 0 && lines[matchIndex - 1].includes('if (__DEV__)')) {
            return match;
          }
          
          // Check if current line is inside a __DEV__ block
          if (match.includes('__DEV__')) {
            return match;
          }

          const isDevMethod = ['log', 'info', 'debug', 'warn'].includes(method);
          const isErrorMethod = method === 'error';

          if (isDevMethod) {
            // Wrap with __DEV__
            fileChanges++;
            this.results.wrapped++;
            return `${prefix}${indent}if (__DEV__) {\n${prefix}${indent}  ${consoleStatement}\n${prefix}${indent}}`;
          } else if (isErrorMethod) {
            // Check for sensitive data patterns
            const sanitized = this.sanitizeErrorStatement(consoleStatement);
            if (sanitized !== consoleStatement) {
              fileChanges++;
              this.results.sanitized++;
              return `${prefix}${indent}${sanitized}`;
            } else {
              this.results.skipped++;
              return match;
            }
          }

          return match;
        }
      );

      // Only write if changes were made
      if (fileChanges > 0) {
        fs.writeFileSync(filePath, content, 'utf-8');
        this.totalChanges += fileChanges;
        return fileChanges;
      }
      
      return 0;
    } catch (error) {
      this.errors.push({ file: filePath, error: error.message });
      return 0;
    }
  }

  // Sanitize error statements
  sanitizeErrorStatement(statement) {
    const sensitivePatterns = [
      /password/i,
      /token/i,
      /secret/i,
      /key/i,
      /email/i,
      /user.*data/i,
      /auth.*data/i
    ];

    const hasSensitiveData = sensitivePatterns.some(pattern => pattern.test(statement));
    
    if (hasSensitiveData) {
      return `${statement} // TODO: Review for sensitive data`;
    }
    
    return statement;
  }

  // Process files in smaller batches
  async processBatch(files, batchIndex) {
    if (__DEV__) {
  async processBatch(files, batchIndex) {
      console.log(`📦 Processing batch ${batchIndex + 1}/${Math.ceil(files.length / 5)} (${Math.min(5, files.length - batchIndex * 5)} files)`);
  async processBatch(files, batchIndex) {
    }
    
    let batchChanges = 0;
    const endIndex = Math.min(batchIndex * 5 + 5, files.length);
    
    for (let i = batchIndex * 5; i < endIndex; i++) {
      const file = files[i];
      const changes = this.processFile(file);
      if (changes > 0) {
        if (__DEV__) {
      if (changes > 0) {
          if (__DEV__) {
            console.log(`  ✅ ${file}: ${changes} changes`);
          }
      if (changes > 0) {
        }
        batchChanges += changes;
      }
      this.processedFiles++;
    }
    
    if (__DEV__) {
    }
    
      if (__DEV__) {
    
        console.log(`📊 Batch complete: ${batchChanges} changes made`);
    
      }
    }
    
    }
    return batchChanges;
  }

  // Main execution
  async run() {
    if (__DEV__) {
  async run() {
      if (__DEV__) {
        console.log('🚀 Starting FINAL console statement fixing process...\n');
      }
  async run() {
    }
    
    // Find files with actual console statements
    if (__DEV__) {
    // Find files with actual console statements
      if (__DEV__) {
        console.log('🔍 Finding files with console statements...');
      }
    // Find files with actual console statements
    }
    const filesWithConsole = this.findFilesWithConsole();
    
    if (__DEV__) {
    const filesWithConsole = this.findFilesWithConsole();
    
      if (__DEV__) {
    
        console.log(`📈 Found ${filesWithConsole.length} files with console statements`);
    
      }
    const filesWithConsole = this.findFilesWithConsole();
    
    }
    
    if (filesWithConsole.length === 0) {
      if (__DEV__) {
    if (filesWithConsole.length === 0) {
        if (__DEV__) {
          console.log('✨ No files need processing!');
        }
    if (filesWithConsole.length === 0) {
      }
      return;
    }

    // Process files in batches of 5
    const totalBatches = Math.ceil(filesWithConsole.length / 5);
    
    for (let i = 0; i < totalBatches; i++) {
      await this.processBatch(filesWithConsole, i);
      
      // Small delay between batches
      if (i < totalBatches - 1) {
        await new Promise(resolve => setTimeout(resolve, 100));
      }
    }

    this.printSummary();
  }

  // Print final summary
  printSummary() {
    if (__DEV__) {
  printSummary() {
      console.log('\n' + '='.repeat(60));
  printSummary() {
    }
    if (__DEV__) {
      console.log('📊 FINAL SUMMARY');
    }
    if (__DEV__) {
      console.log('='.repeat(60));
    }
    if (__DEV__) {
      console.log(`📁 Files processed: ${this.processedFiles}`);
    }
    if (__DEV__) {
      console.log(`🔧 Total changes: ${this.totalChanges}`);
    }
    if (__DEV__) {
      console.log(`🛡️  Statements wrapped with __DEV__: ${this.results.wrapped}`);
    }
    if (__DEV__) {
      console.log(`🔍 Error statements sanitized: ${this.results.sanitized}`);
    }
    if (__DEV__) {
      console.log(`⏭️  Statements skipped: ${this.results.skipped}`);
    }
    
    if (this.errors.length > 0) {
      if (__DEV__) {
    if (this.errors.length > 0) {
        if (__DEV__) {
          console.log(`\n❌ Errors encountered: ${this.errors.length}`);
        }
    if (this.errors.length > 0) {
      }
      this.errors.forEach(({ file, error }) => {
        if (__DEV__) {
      this.errors.forEach(({ file, error }) => {
          if (__DEV__) {
            console.log(`  - ${file}: ${error}`);
          }
      this.errors.forEach(({ file, error }) => {
        }
      });
    }
    
    if (__DEV__) {
    }
    
      if (__DEV__) {
    
        console.log('\n✨ Console statement fixing complete!');
    
      }
    }
    
    }
    
    // Verification
    if (__DEV__) {
    // Verification
      if (__DEV__) {
        console.log('\n🔍 Running verification...');
      }
    // Verification
    }
    this.runVerification();
  }

  // Verify the changes
  runVerification() {
    try {
      // Count actual console statements (not false positives)
      const command = `find . -type f \\( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \\) -not -path "./node_modules/*" -not -path "./.expo/*" -not -path "./dist/*" | xargs grep -c "console\\.[a-zA-Z]" 2>/dev/null | awk -F: '{sum+=$2} END {print sum}'`;
      const remaining = execSync(command, { encoding: 'utf-8' }).trim();
      if (__DEV__) {
      const remaining = execSync(command, { encoding: 'utf-8' }).trim();
        if (__DEV__) {
          console.log(`📈 Console statements remaining: ${remaining || 0}`);
        }
      const remaining = execSync(command, { encoding: 'utf-8' }).trim();
      }
      
      // Check for unwrapped dev console statements
      const unwrappedCommand = `find . -type f \\( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \\) -not -path "./node_modules/*" -not -path "./.expo/*" -not -path "./dist/*" | xargs grep -l "console\\.[a-zA-Z]" 2>/dev/null | xargs grep -L "__DEV__" 2>/dev/null | wc -l`;
      const unwrapped = execSync(unwrappedCommand, { encoding: 'utf-8' }).trim();
      if (__DEV__) {
      const unwrapped = execSync(unwrappedCommand, { encoding: 'utf-8' }).trim();
        if (__DEV__) {
          console.log(`⚠️  Files with potentially unwrapped dev console statements: ${unwrapped || 0}`);
        }
      const unwrapped = execSync(unwrappedCommand, { encoding: 'utf-8' }).trim();
      }
      
      // Show sample unwrapped statements (actual console calls)
      if (__DEV__) {
      // Show sample unwrapped statements (actual console calls)
        if (__DEV__) {
          console.log('\n📋 Sample remaining console statements:');
        }
      // Show sample unwrapped statements (actual console calls)
      }
      try {
        const sampleCommand = `find . -type f \\( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \\) -not -path "./node_modules/*" -not -path "./.expo/*" -not -path "./dist/*" | xargs grep -n "console\\.[a-zA-Z]" 2>/dev/null | grep -v "__DEV__" | head -5`;
        const samples = execSync(sampleCommand, { encoding: 'utf-8' }).trim();
        if (__DEV__) {
        const samples = execSync(sampleCommand, { encoding: 'utf-8' }).trim();
          if (__DEV__) {
            console.log(samples || 'No unwrapped console statements found');
          }
        const samples = execSync(sampleCommand, { encoding: 'utf-8' }).trim();
        }
      } catch (e) {
        if (__DEV__) {
      } catch (e) {
          if (__DEV__) {
            console.log('No unwrapped console statements found');
          }
      } catch (e) {
        }
      }
      
    } catch (error) {
      if (__DEV__) {
    } catch (error) {
        if (__DEV__) {
          console.log('❌ Verification failed:', error.message);
        }
    } catch (error) {
      }
    }
  }
}

// Run the fixer
const fixer = new ConsoleStatementFixerFinal();
fixer.run().catch(console.error);