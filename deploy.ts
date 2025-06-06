// deploy.ts
import { Application } from "https://deno.land/x/oak@v12.6.1/mod.ts";
import { bot } from "./main.ts";

const app = new Application();

// Handle webhook updates
app.use(async (ctx) => {
  try {
    const body = await ctx.request.body().value;
    await bot.handleUpdate(body);
    ctx.response.status = 200;
  } catch (err) {
    console.error(err);
    ctx.response.status = 500;
  }
});

// Start server
const PORT = Deno.env.get("PORT") || 8000;
console.log(`Server running on port ${PORT}`);
await app.listen({ port: Number(PORT) });
