# FIFA World Cup AI Agent

An AI-powered chat agent specialized in FIFA World Cup history, built from scratch in Python using the GitHub Models API with Wikipedia, DuckDuckGo Search, persistent memory, and intelligent tool selection. It answers questions about past World Cups, pulls live information when needed, and tracks its own performance on a real-time dashboard.

## Features

### Knowledge Retrieval
- Wikipedia lookup
- DuckDuckGo web search
- Live football scores
- Intelligent search fallback

### Conversation
- Persistent conversation memory
- Context-aware follow-up questions
- Query caching

### Developer Features
- Live performance dashboard
- Tool usage statistics
- Response timing
- Cache statistics

## Tech Stack

- **Language:** Python
- **LLM:** GitHub Models API
- **Tools/Integrations:** DuckDuckGo Search, Wikipedia API, live football score API
- **Dashboard:** Real-time stats display (refreshes on every response)

## Architecture diagram

User
   │
   ▼
Conversation Memory
   │
   ▼
Cache
   │
   ▼
Tool Selection
 ┌──────┴────────┐
 ▼               ▼
Wikipedia    Web Search
      │
      ▼
 GitHub Models
      │
      ▼
 Update Memory
      │
      ▼
  Response

## How It Works

1. User asks a question about a World Cup topic.
2. The agent checks its cache first — if it's seen a similar query before, it returns the cached result instantly.
3. If not cached, the agent decides which tool(s) to use (web search, Wikipedia, or live scores) to gather the information it needs.
4. It generates a response using the GitHub Models API, grounded in the retrieved information.
5. The response and query are stored in memory for context in later turns.
6. The dashboard updates with the latest stats: response time, cache hit/miss, tool usage, and the current topic/player.

## Setup & Usage

```bash
# Clone the repo
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>

# Install dependencies
pip install -r requirements.txt

# Add GitHub token
# Create a .env file with:
# GITHUB_TOKEN=your_token_here

# Run the agent
python agent.py
```

## Example Conversation

Prompt: Who won the 2018 World Cup?

Agent: 🧠 Reasoning: To find out who won the 2018 FIFA World Cup, I will check the details specifically related to the tournament from the summary provided in the Wikipedia lookup to identify the winning team.

✅ Answer: The winner of the 2018 FIFA World Cup was France, who defeated Croatia 4-2 in the final match.

Prompt: Who was the leading goalscorer?

Agent: 🧠 Reasoning: The web search has returned some relevant resources mentioning the top goal scorers for France during the 2018 World Cup. I'll check these resources for the leading goalscorer information specifically related to the French team.

✅ Answer: The leading goalscorer for France during the 2018 World Cup was Antoine Griezmann, who scored 4 goals throughout the tournament.

Prompt: What club was he playing for?

Agent: 🧠 Reasoning: To find out which club Antoine Griezmann was playing for during the 2018 FIFA World Cup, I will check the information provided in the Wikipedia summary regarding his club career.

✅ Answer: During the 2018 FIFA World Cup, Antoine Griezmann was playing for Atlético Madrid in La Liga.


## What I Learned

Building this project involved working through challenges like managing API rate limits with caching, designing a lightweight memory system to give the agent conversational context, and building a dashboard that updates live alongside the chat — all as a self-directed project outside of coursework.

## Future Improvements

- Automated evaluation suite
- Confidence scoring
- Web interface
- Multiple-source verification

## Challenges & Fixes

Intelligent search fallback — Early on, if the first search came back irrelevant, the agent would sometimes generate an answer anyway rather than admit it didn't have the information. I added fallback logic so that when a lookup fails or returns weak results, the agent automatically retries with an alternative search query instead of guessing — this cut down on unsupported or made-up answers significantly.

Pronoun and reference resolution — Follow-up questions using pronouns (e.g. "how many goals did he score?" or "when did the team qualify?") were initially breaking the agent, since each query was treated in isolation. I extended the memory system to track the current topic and player across turns, so the agent can resolve "he" or "the team" against what was actually being discussed, instead of losing context between messages.

Search accuracy — The agent occasionally pulled incorrect information from search results. I worked on improving how results were selected and cross-referenced (e.g. leaning more on Wikipedia for factual lookups vs. general search) to reduce the rate of wrong answers being surfaced.

## Screenshots
![Agent Dashboard after several conversations](Dashboard.png)

![Prompt](Prompt.png)

Built as a personal project to combine an interest in football with hands-on AI agent development.
