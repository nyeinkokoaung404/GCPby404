// deploy.ts
import { Application, Router } from "https://deno.land/x/oak@v12.6.1/mod.ts";
import { bot, runBot } from "./main.ts";

const app = new Application();
const router = new Router();

// Webhook handler
router.post("/webhook", async (ctx) => {
  try {
    const body = await ctx.request.body().value;
    await bot.handleUpdate(body);
    ctx.response.status = 200;
  } catch (err) {
    console.error("Webhook error:", err);
    ctx.response.status = 500;
  }
});

// Health check endpoint
router.get("/", (ctx) => {
  ctx.response.body = "Bot is running";
});

app.use(router.routes());
app.use(router.allowedMethods());

// Start the bot and server
const PORT = Deno.env.get("PORT") || 8000;
console.log(`Server running on port ${PORT}`);

// Start both the web server and the bot
Promise.all([
  app.listen({ port: Number(PORT) }),
  runBot()
]).catch(err => {
  console.error("Failed to start:", err);
  Deno.exit(1);
});
