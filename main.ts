// main.ts
import { Bot } from "https://deno.land/x/grammy@v1.20.3/mod.ts";
import { run, sequentialize } from "https://deno.land/x/grammy_runner@v2.0.3/mod.ts";
import { freeStorage } from "https://deno.land/x/grammy_storages@v2.3.1/free/src/mod.ts";

// Type definitions
interface SessionData {
  cookies: string;
  orgs: OrgData[];
  devUrls: DevUrl[];
}

interface OrgData {
  id: string;
  name: string;
  createdAt: Date;
}

interface DevUrl {
  url: string;
  createdAt: Date;
  expiresAt: Date;
}

// Load environment variables
const BOT_TOKEN = Deno.env.get('BOT_TOKEN') || '7903246802:AAFBD6P12ZmGZPvD5vs2fLUqazUkTH2safE';
const API_ID = parseInt(Deno.env.get('API_ID') || '24785831');
const API_HASH = Deno.env.get('API_HASH') || '81b87c7c85bf0c4ca15ca94dcea3fb95';
const OWNER_ID = parseInt(Deno.env.get('OWNER_ID') || '1273841502');
const DENO_DEPLOY_URL = Deno.env.get('DENO_DEPLOY_URL') || 'https://4-0-4-gcpbydeno-64.deno.dev';

// Validate environment variables
if (!BOT_TOKEN) throw new Error("BOT_TOKEN is required");
if (!API_ID) throw new Error("API_ID is required");
if (!API_HASH) throw new Error("API_HASH is required");
if (!OWNER_ID) throw new Error("OWNER_ID is required");

// Initialize bot with storage
export const bot = new Bot(BOT_TOKEN);
const storage = freeStorage<SessionData>(bot.token);

// Middleware
bot.use(sequentialize(ctx => ctx.from?.id.toString()));
bot.use(async (ctx, next) => {
  ctx.session = await storage.read(ctx.from?.id.toString()) || {
    cookies: "",
    orgs: [],
    devUrls: []
  };
  await next();
  await storage.write(ctx.from?.id.toString(), ctx.session);
});

// Error handling
bot.catch(err => {
  console.error("Bot error:", err);
});

// Start command
bot.command("start", ctx => ctx.reply("Welcome to the Deno-Telegram Integration Bot!"));

// /deno command handler
bot.command("deno", async (ctx) => {
  if (ctx.from?.id !== OWNER_ID) {
    return ctx.reply("🚫 Access denied. Only owner can use this command.");
  }

  try {
    // Show loading message
    await ctx.reply("🔄 Processing your request...");

    // Call your existing 4-0-4-gcpbydeno project
    const response = await fetch(DENO_DEPLOY_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        command: "generate",
        userId: ctx.from.id.toString(),
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    
    // Update session data
    if (result.cookies) {
      ctx.session.cookies = result.cookies;
    }

    if (result.org) {
      ctx.session.orgs.push({
        id: result.org.id,
        name: result.org.name,
        createdAt: new Date()
      });
    }

    if (result.devUrl) {
      ctx.session.devUrls.push({
        url: result.devUrl.url,
        createdAt: new Date(),
        expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000) // 30 days
      });
    }

    // Prepare response message
    let message = "✅ <b>Deno Project Generated Successfully!</b>\n\n";
    
    if (result.cookies) {
      message += `🍪 <b>Cookies Updated:</b>\n<code>${result.cookies.substring(0, 20)}...</code>\n\n`;
    }
    
    if (result.org) {
      message += `🏢 <b>Organization Created:</b>\n${result.org.name} (ID: ${result.org.id})\n\n`;
    }
    
    if (result.devUrl) {
      message += `🔗 <b>Dev URL:</b>\n<code>${result.devUrl.url}</code>\n\n`;
      message += `⏳ <b>Expires:</b> ${new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toLocaleDateString()}`;
    }

    await ctx.reply(message, { parse_mode: "HTML" });

  } catch (error) {
    console.error("Error in /deno command:", error);
    await ctx.reply("❌ Error generating Deno project. Please try again later.");
  }
});

// Export the run function for deployment
export const runBot = () => {
  console.log("Starting bot...");
  return run(bot, {
    runner: {
      fetch: {
        timeout: 30, // seconds
      },
      handlerTimeout: 5, // minutes
      retryInterval: 3, // seconds
    },
  });
};

// Self-invocation for local testing
if (import.meta.main) {
  runBot().catch(err => console.error("Bot failed:", err));
}
