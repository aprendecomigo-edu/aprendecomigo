#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Configuration
const BATCH_SIZE = 10;
const EXTENSIONS = ['.ts', '.tsx', '.js', '.jsx'];
const EXCLUDE_PATTERNS = [
  'node_modules',
  '.expo',
  'dist',
  '.git'
];

// Console methods to wrap with __DEV__
const DEV_CONSOLE_METHODS = ['log', 'info', 'debug', 'warn'];
const ERROR_CONSOLE_METHODS = ['error'];

class ConsoleStatementFixerV2 {
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

  // Find all TypeScript/JavaScript files
  findTargetFiles() {
    try {
      const command = `find . -type f \\( ${EXTENSIONS.map(ext => `-name "*${ext}"`).join(' -o ')} \\) ${EXCLUDE_PATTERNS.map(pattern => `-not -path "./${pattern}/*"`).join(' ')}`;
      const output = execSync(command, { encoding: 'utf-8' });
      return output.trim().split('\n').filter(Boolean);
    } catch (error) {
      console.error('Error finding files:', error.message);
      return [];
    }
  }

  // Check if file has console statements
  hasConsoleStatements(filePath) {
    try {
      const content = fs.readFileSync(filePath, 'utf-8');
      return /console\.[a-zA-Z]+\s*\(/.test(content);
    } catch (error) {
      return false;
    }
  }

  // Process a single file
  processFile(filePath) {
    try {
      const originalContent = fs.readFileSync(filePath, 'utf-8');
      let content = originalContent;
      let fileChanges = 0;

      // Split content into lines for line-by-line processing
      const lines = content.split('\n');
      const processedLines = [];

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        
        // Check if line contains console statement
        const consoleMatch = line.match(/^(\s*)(.*console\.(log|info|debug|warn|error)\s*\([^)]*\);?.*)$/);
        
        if (consoleMatch) {
          const [, indent, consoleLine, method] = consoleMatch;
          
          // Skip if already wrapped with __DEV__
          if (line.includes('if (__DEV__)') || 
              (i > 0 && lines[i - 1].includes('if (__DEV__)'))) {
            processedLines.push(line);
            continue;
          }

          if (DEV_CONSOLE_METHODS.includes(method)) {
            // Wrap with __DEV__
            processedLines.push(`${indent}if (__DEV__) {`);
            processedLines.push(`${indent}  ${consoleLine}`);
            processedLines.push(`${indent}}`);
            this.results.wrapped++;
            fileChanges++;
          } else if (ERROR_CONSOLE_METHODS.includes(method)) {
            // Keep error statements but check for sensitive data patterns
            const sanitized = this.sanitizeErrorStatement(consoleLine);
            if (sanitized !== consoleLine) {
              processedLines.push(`${indent}${sanitized}`);
              this.results.sanitized++;
              fileChanges++;
            } else {
              processedLines.push(line);
              this.results.skipped++;
            }
          } else {
            processedLines.push(line);
          }
        } else {
          processedLines.push(line);
        }
      }

      // Only write if changes were made
      if (fileChanges > 0) {
        const newContent = processedLines.join('\n');
        fs.writeFileSync(filePath, newContent, 'utf-8');
        this.totalChanges += fileChanges;
        return fileChanges;
      }
      
      return 0;
    } catch (error) {
      this.errors.push({ file: filePath, error: error.message });
      return 0;
    }
  }

  // Sanitize error statements (remove potential sensitive data)
  sanitizeErrorStatement(statement) {
    // Look for patterns that might contain sensitive data
    const sensitivePatterns = [
      /password/i,
      /token/i,
      /secret/i,
      /key/i,
      /email/i,
      /user.*data/i,
      /auth.*data/i
    ];

    // If the statement contains sensitive patterns, add a comment
    const hasSensitiveData = sensitivePatterns.some(pattern => pattern.test(statement));
    
    if (hasSensitiveData) {
      return `${statement} // TODO: Review for sensitive data`;
    }
    
    return statement;
  }

  // Process files in batches
  async processBatch(files, batchIndex, groupName) {
    if (__DEV__) {
      console.log(`\n📦 Processing ${groupName} batch ${batchIndex + 1}/${Math.ceil(files.length / BATCH_SIZE)} (${files.length} files)`);
    }
    
    let batchChanges = 0;
    
    for (const file of files) {
      const changes = this.processFile(file);
      if (changes > 0) {
        if (__DEV__) {
          console.log(`  ✅ ${file}: ${changes} changes`);
        }
        batchChanges += changes;
      }
      this.processedFiles++;
    }
    
    if (__DEV__) {
      console.log(`📊 Batch complete: ${batchChanges} changes made`);
    }
    return batchChanges;
  }

  // Main execution
  async run() {
    if (__DEV__) {
      console.log('🚀 Starting console statement fixing process (V2)...\n');
    }
    
    // Find all target files
    if (__DEV__) {
      console.log('🔍 Finding target files...');
    }
    const allFiles = this.findTargetFiles();
    
    // Filter to only files with console statements
    if (__DEV__) {
      console.log('📋 Filtering files with console statements...');
    }
    const filesWithConsole = allFiles.filter(file => this.hasConsoleStatements(file));
    
    if (__DEV__) {
      console.log(`📈 Found ${filesWithConsole.length} files with console statements`);
    }
    
    if (filesWithConsole.length === 0) {
      if (__DEV__) {
        console.log('✨ No files need processing!');
      }
      return;
    }

    // Group files by priority
    const priorityGroups = this.groupFilesByPriority(filesWithConsole);
    
    // Process each priority group
    for (const [priority, files] of Object.entries(priorityGroups)) {
      if (files.length === 0) continue;
      
      if (__DEV__) {
        console.log(`\n🎯 Processing ${priority} files (${files.length} files)...`);
      }
      
      // Split into batches
      const batches = this.createBatches(files, BATCH_SIZE);
      
      for (let i = 0; i < batches.length; i++) {
        await this.processBatch(batches[i], i, priority);
        
        // Small delay between batches to avoid overwhelming
        if (i < batches.length - 1) {
          await this.sleep(100);
        }
      }
    }

    this.printSummary();
  }

  // Group files by priority for processing order
  groupFilesByPriority(files) {
    const groups = {
      'HIGH PRIORITY': [],
      'APP ROUTES': [],
      'COMPONENTS': [],
      'HOOKS': [],
      'UTILS & SERVICES': [],
      'OTHER': []
    };

    files.forEach(file => {
      if (file.includes('/payment') || file.includes('/auth') || file.includes('/user')) {
        groups['HIGH PRIORITY'].push(file);
      } else if (file.includes('/app/')) {
        groups['APP ROUTES'].push(file);
      } else if (file.includes('/components/')) {
        groups['COMPONENTS'].push(file);
      } else if (file.includes('/hooks/')) {
        groups['HOOKS'].push(file);
      } else if (file.includes('/utils/') || file.includes('/services/') || file.includes('/lib/') || file.includes('/api/')) {
        groups['UTILS & SERVICES'].push(file);
      } else {
        groups['OTHER'].push(file);
      }
    });

    return groups;
  }

  // Create batches from array
  createBatches(array, size) {
    const batches = [];
    for (let i = 0; i < array.length; i += size) {
      batches.push(array.slice(i, i + size));
    }
    return batches;
  }

  // Sleep utility
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Print final summary
  printSummary() {
    if (__DEV__) {
      console.log('\n' + '='.repeat(60));
    }
    if (__DEV__) {
      console.log('📊 FINAL SUMMARY (V2)');
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
        console.log(`\n❌ Errors encountered: ${this.errors.length}`);
      }
      this.errors.forEach(({ file, error }) => {
        if (__DEV__) {
          console.log(`  - ${file}: ${error}`);
        }
      });
    }
    
    if (__DEV__) {
      console.log('\n✨ Console statement fixing complete!');
    }
    
    // Verification
    if (__DEV__) {
      console.log('\n🔍 Running verification...');
    }
    this.runVerification();
  }

  // Verify the changes
  runVerification() {
    try {
      const command = `find . -type f \\( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \\) -not -path "./node_modules/*" -not -path "./.expo/*" -not -path "./dist/*" | xargs grep -c "console\\." | awk -F: '{sum+=$2} END {print sum}'`;
      const remaining = execSync(command, { encoding: 'utf-8' }).trim();
      if (__DEV__) {
        console.log(`📈 Console statements remaining: ${remaining}`);
      }
      
      // Check for unwrapped dev console statements
      const unwrappedCommand = `find . -type f \\( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \\) -not -path "./node_modules/*" -not -path "./.expo/*" -not -path "./dist/*" | xargs grep -l "^[[:space:]]*console\\.(log\\|info\\|debug\\|warn)" | wc -l`;
      const unwrapped = execSync(unwrappedCommand, { encoding: 'utf-8' }).trim();
      if (__DEV__) {
        console.log(`⚠️  Files with unwrapped dev console statements: ${unwrapped}`);
      }
      
      // Show sample unwrapped statements
      if (__DEV__) {
        console.log('\n📋 Sample unwrapped console statements:');
      }
      try {
        const sampleCommand = `find . -type f \\( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \\) -not -path "./node_modules/*" -not -path "./.expo/*" -not -path "./dist/*" | xargs grep -n "^[[:space:]]*console\\.(log\\|info\\|debug\\|warn)" | head -5`;
        const samples = execSync(sampleCommand, { encoding: 'utf-8' }).trim();
        if (__DEV__) {
          console.log(samples);
        }
      } catch (e) {
        if (__DEV__) {
          console.log('No unwrapped statements found');
        }
      }
      
    } catch (error) {
      if (__DEV__) {
        console.log('❌ Verification failed:', error.message);
      }
    }
  }
}

// Run the fixer
const fixer = new ConsoleStatementFixerV2();
fixer.run().catch(console.error);