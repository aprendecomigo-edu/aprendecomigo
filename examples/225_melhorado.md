# Exemplo: Issue 225 com template melhorado

## 📋 Descrição do Problema

### 🔍 Estado atual:
Ao clicar no botão de "Log out", o utilizador é redirecionado para uma página "Page Not Found".

### ❌ O que está mal:
Em vez de ser feito o logout e o utilizador ser redirecionado para a página de login, aparece uma página de erro ("Page Not Found"). Isto impede os utilizadores de fazerem logout corretamente, criando uma experiência frustrante e potenciais problemas de segurança se a sessão não for encerrada adequadamente.

### ✅ O que é suposto acontecer:
Quando o utilizador clica em "Log out", deve ser feita a saída da conta e o utilizador deve ser encaminhado para a página de login (/login/).

## 🔄 Como reproduzir:

1. Fazer login na plataforma como qualquer tipo de utilizador
2. Navegar para qualquer página do dashboard
3. Clicar no botão "Log out" no menu de utilizador
4. Observar que aparece "Page Not Found" em vez de ser redirecionado para login

## 📱 Ambiente:
- **Dispositivo**: [x] Desktop [ ] Mobile [ ] Tablet
- **Browser**: Chrome/Firefox/Safari (todos afetados)
- **Role do Utilizador**: [x] School Owner [x] Professor [x] Aluno [x] Pai

## 📊 Prioridade:
- [x] 🚨 Alta (funcionalidade principal afetada) 

**Razão da prioridade**: Logout é uma funcionalidade de segurança crítica que deve funcionar corretamente.

---

**Para Developers:**
- [ ] Bug reproduzido
- [ ] Causa identificada (provavelmente URL de logout incorreto ou view em falta)
- [ ] Testes criados para validar logout flow
- [ ] Correção testada em todos os tipos de utilizador