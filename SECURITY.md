# Política de segurança

## Versões suportadas

A versão mais recente da linha `0.1.x` recebe correções de segurança durante o desenvolvimento inicial.

## Relato responsável

Não publique detalhes exploráveis em uma issue pública. Use o recurso privado **Security advisories → Report a vulnerability** do repositório. Inclua impacto, versão, passos mínimos de reprodução e mitigação sugerida, sem dados reais de usuários.

O projeto buscará confirmar o recebimento em até 3 dias úteis e comunicar escopo e correção de forma coordenada. Não há programa de recompensa financeira.

## Operação segura

- Use OIDC e PostgreSQL para ambientes multiusuário.
- Mantenha secrets somente no gerenciador do ambiente.
- Aplique migrações e atualizações pelo lockfile.
- Monitore auditorias de dependências, Dependabot e CodeQL.
- Faça backups criptografados e testes de restauração.
- Não exponha diretamente o Streamlit à internet sem TLS e controles do provedor.

