# Melhorias nos Templates de Bug Reports

## 📖 Resumo das Melhorias

Os templates de bug reports foram melhorados para proporcionar relatórios mais completos e estruturados, mantendo a simplicidade para a equipa.

## 🔄 Antes vs Depois

### Formato Anterior (Original)
```markdown
1. **Estado atual:** [descrição]
2. **O que está mal:** [explicação]  
3. **O que é suposto acontecer:** [comportamento esperado]
```

### Formato Melhorado
```markdown
## 📋 Descrição do Problema

### 🔍 Estado atual:
[Descrição detalhada com contexto]

### ❌ O que está mal:
[Explicação do impacto e problema]

### ✅ O que é suposto acontecer:
[Comportamento esperado claro]

## 🔄 Como reproduzir:
[Passos específicos]

## 📱 Ambiente:
[Informação de dispositivo, browser, role]

## 📊 Prioridade:
[Classificação de urgência]
```

## ✨ Principais Melhorias

### 1. **Estrutura Visual Melhorada**
- ✅ Emojis para melhor organização visual
- ✅ Secções claramente definidas
- ✅ Headers consistentes

### 2. **Informação de Contexto**
- ✅ Passos para reproduzir o bug
- ✅ Informação do ambiente (dispositivo, browser, role)
- ✅ Classificação de prioridade
- ✅ Espaço para capturas de ecrã

### 3. **Fluxo de Desenvolvimento**
- ✅ Checklist para developers
- ✅ Critérios de aceitação
- ✅ Tracking de reprodução e correção

### 4. **Flexibilidade**
- ✅ Template completo (`bug_report.md`) para bugs complexos
- ✅ Template simples (`bug_simple.md`) para reports rápidos
- ✅ Mantém a estrutura core original (3 secções principais)

## 📁 Arquivos Criados

1. **`.github/ISSUE_TEMPLATE/bug_report.md`** - Template completo
2. **`.github/ISSUE_TEMPLATE/bug_simple.md`** - Template simplificado  
3. **`.github/ISSUE_TEMPLATE/config.yml`** - Configuração dos templates
4. **`examples/225_melhorado.md`** - Exemplo de aplicação do template melhorado

## 🎯 Benefícios

### Para Quem Reporta Bugs:
- Estrutura clara para descrever problemas
- Lembretes para incluir informação importante
- Templates adaptados ao contexto (simples vs completo)

### Para Developers:
- Informação consistente e completa
- Priorização clara dos bugs
- Checklist de correção integrado
- Melhor tracking do processo de resolução

### Para a Equipa:
- Redução de vai-e-vem para clarificações
- Bugs melhor categorizados e priorizados
- Processo de QA mais estruturado

## 📋 Como Usar

### Para Bug Reports Rápidos:
Use o template **"Bug Report (Simples)"** - mantém a essência das 3 secções originais com melhorias visuais e contexto mínimo.

### Para Bugs Complexos:
Use o template **"Relatório de Bug"** completo - inclui todas as secções para documentação completa.

## 🔄 Migração Gradual

Os templates existem lado-a-lado com o formato atual:
- Issues existentes mantêm o formato original
- Novos issues podem usar os templates melhorados
- Equipa pode escolher qual template usar baseado na complexidade do bug

## 📝 Exemplo de Melhoria

Veja `examples/225_melhorado.md` para comparar como o Issue #225 ficaria com o template melhorado, mantendo a informação original mas com melhor estrutura e contexto adicional.