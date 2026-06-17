# 🤖 Projeto Optimus: Extrator de Dados via API

Automação desenvolvida por mim para otimizar o fluxo de informações e a extração de dados dentro da TB Serviços, resolvendo gargalos reais de infraestrutura corporativa.

## 📋 Sobre o Projeto
A solução foi arquitetada e criada para substituir rotinas instáveis de extração manual na empresa. O sistema consome uma API externa e trata os dados em memória para gerar relatórios operacionais de forma autônoma. O objetivo central alcançado é a eliminação de erros de *Timeout* e *Out of Memory* no servidor, garantindo 100% de estabilidade nas operações diárias.

## 🚀 Tecnologias Utilizadas
* **Python 3**
* **Pandas:** Para manipulação de DataFrames e limpeza de dados (expurgo de duplicatas).
* **Requests:** Para comunicação HTTP/RESTful e autenticação via token JWT.

## ⚙️ Arquitetura e Soluções
* **Loteamento Temporal (Time-Batching):** O script fatia dinamicamente grandes volumes de dados em intervalos de 5 meses para não sobrecarregar a API da empresa.
* **Tolerância a Falhas:** Envelopamento de requisições com tratamento de exceções, permitindo que o robô ignore instabilidades de rede e salve o progresso parcial sem perder os dados já processados.
* **Gerenciamento de Memória:** Isolamento de escopo por *endpoint* acoplado ao *Garbage Collector* do Python, protegendo o servidor.
* **Inteligência de Roteamento:** O código detecta o usuário do SO e mapeia automaticamente caminhos de rede ou diretórios de *fallback* para salvar os arquivos Excel (`.xlsx`).

## 👨‍💻 Autor
**Gabriel Viana**
