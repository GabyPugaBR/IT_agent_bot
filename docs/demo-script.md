# Demo Script

## Recommended Demo Flow
1. Open the `Constellations.com` homepage and point out the visible `IT Agent` entry points.
2. Open the chatbot and ask: `How do I reset my password?`
3. Explain that the knowledge agent answers first from the knowledge base.
4. Then send: `Reset password for student15`
5. Show the workflow result card with a temporary password and policy information.
6. Ask: `Wi-Fi is not working in Room 204`
7. Show that the request now routes to the knowledge path instead of getting stuck in password workflow.
8. Ask: `Can you check the weather?`
9. Explain that the bot cannot help directly, so it offers appointment scheduling.
10. Click `Yes, show appointments` and then book one slot.
11. Ask for `request software/hardware`
12. Fill out the form and submit it.
13. Close the chatbot by typing `exit chat`.

## Talking Points
- The system is intentionally multi-agent, not a single monolithic chatbot.
- MCP is used for tool access and simulated automation.
- RAG is grounded in a school-specific knowledge base.
- Memory allows continuity across turns.
- Docker makes the project portable and reproducible.

