const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');
const fs = require('fs');
const jsdom = require('jsdom');
const { JSDOM } = jsdom;

// ==================== [ CONFIGURATION ] ====================
const TOKEN = '8855372052:AAHJ04PSoc6nBSAP71upW0N6gdSmnNYkdz8';
const ADMIN_ID = 8419760844;
const DEVELOPER_HANDLE = '@LEADER_NIROB_GX';
const DEVELOPER_LINK = 'https://t.me/NIROB_GX_LEADER';

const bot = new TelegramBot(TOKEN, { polling: true });

// ডাটাবেস ভেরিয়েবল (মেমোরি বেসড)
let bannedUsers = new Set();
let allUsers = new Set();
let userState = {}; // স্টেট ট্রেকিং

// ==================== [ KEYBOARDS ] ====================

// ১. সাধারণ ইউজার মেনু
const userMenu = {
    reply_markup: {
        keyboard: [
            [{ text: "🔗 Link to Decode" }, { text: "📜 HTML to Decode" }],
            [{ text: "👨‍💻 Developer Info" }]
        ],
        resize_keyboard: true
    }
};

// ২. অ্যাডমিন প্যানেল মেনু
const adminMenu = {
    reply_markup: {
        keyboard: [
            [{ text: "🚫 Ban User" }, { text: "✅ Unban User" }],
            [{ text: "📊 All Users" }, { text: "🔙 User Mode" }]
        ],
        resize_keyboard: true
    }
};

// ==================== [ HTML DECODING LOGIC ] ====================
function processAndCleanHTML(inputHtml) {
    try {
        const dom = new JSDOM(inputHtml);
        const { document } = dom.window;

        // অ্যান্টি-ইনস্পেক্ট, রিডাইরেক্ট বা ট্র্যাপ কোড রিমুভ করা
        const scripts = document.querySelectorAll('script');
        scripts.forEach(script => {
            const code = script.textContent || '';
            if (
                code.includes('destroyAndRedirect') ||
                code.includes('speechSynthesis') ||
                code.includes('dense_junk_stream') ||
                code.includes('keyCode === 123') ||
                code.includes('debugger') ||
                code.includes('contextmenu')
            ) {
                script.remove();
            }
        });

        return '<!DOCTYPE html>\n' + document.documentElement.outerHTML;
    } catch (err) {
        throw new Error("HTML প্রসেস করতে সমস্যা হয়েছে: " + err.message);
    }
}

// ==================== [ BOT COMMANDS & LOGIC ] ====================

// /start কমান্ড
bot.onText(/\/start/, (msg) => {
    const chatId = msg.chat.id;
    allUsers.add(chatId);

    if (bannedUsers.has(chatId)) {
        return bot.sendMessage(chatId, "❌ **আপনি এই বট থেকে ব্যান হয়ে আছেন!**");
    }

    if (chatId === ADMIN_ID) {
        bot.sendMessage(chatId, `👑 **Welcome Admin!**\n\nআপনি অ্যাডমিন প্যানেলে আছেন। আপনার কন্ট্রোল বাটন নিচে দেওয়া হলো:`, adminMenu);
    } else {
        bot.sendMessage(chatId, `👋 **Welcome to GX HTML Decoder Bot!**\n\nনিচের বাটনগুলো ব্যবহার করে আপনার অপশন সিলেক্ট করুন:`, userMenu);
    }
});

// /admin কমান্ড
bot.onText(/\/admin/, (msg) => {
    if (msg.chat.id !== ADMIN_ID) return;
    bot.sendMessage(msg.chat.id, "🛠 **Admin Panel Loaded!**", adminMenu);
});

// মেসেজ হ্যান্ডলিং
bot.on('message', async (msg) => {
    const chatId = msg.chat.id;
    const text = msg.text ? msg.text.trim() : '';

    if (bannedUsers.has(chatId)) return;
    allUsers.add(chatId);

    // ১. Developer Info
    if (text === "👨‍💻 Developer Info") {
        const devMsg = `💻 **Developer Details**\n\n` +
                       `👤 **Developer:** NIROB GX (${DEVELOPER_HANDLE})\n` +
                       `🔗 **Telegram Direct:** ${DEVELOPER_LINK}\n` +
                       `🛡 **Powered By:** GX BIG COMMUNITY\n\n` +
                       `যেকোনো প্রয়োজনে সরাসরি যোগাযোগ করতে পারেন!`;
        return bot.sendMessage(chatId, devMsg, { parse_mode: 'Markdown' });
    }

    // ২. HTML to Decode
    if (text === "📜 HTML to Decode") {
        userState[chatId] = 'WAITING_FOR_HTML';
        return bot.sendMessage(chatId, "📥 **আপনার Obfuscated / Encrypted HTML কোডটি এখানে পেস্ট করুন অথবা HTML ফাইল হিসাবে পাঠান:**");
    }

    // ৩. Link to Decode
    if (text === "🔗 Link to Decode") {
        userState[chatId] = 'WAITING_FOR_LINK';
        return bot.sendMessage(chatId, "🌐 **যে ওয়েবসাইট বা লিংকের HTML ডিকোড করতে চান, তার URL টি দিন:**\n*(যেমন: https://example.com)*");
    }

    // ৪. অ্যাডমিন: All Users
    if (text === "📊 All Users" && chatId === ADMIN_ID) {
        let userList = `👥 **মোট ইউজার সংখ্যা (${allUsers.size}):**\n\n`;
        allUsers.forEach(id => {
            userList += `• \`${id}\` ${bannedUsers.has(id) ? '❌ (Banned)' : '✅'}\n`;
        });
        return bot.sendMessage(chatId, userList, { parse_mode: 'Markdown' });
    }

    // ৫. অ্যাডমিন: Ban User
    if (text === "🚫 Ban User" && chatId === ADMIN_ID) {
        userState[chatId] = 'WAITING_FOR_BAN_ID';
        return bot.sendMessage(chatId, "⚠️ ব্যান করার জন্য ইউজারের **Telegram ID** দিন:");
    }

    // ৬. অ্যাডমিন: Unban User
    if (text === "✅ Unban User" && chatId === ADMIN_ID) {
        userState[chatId] = 'WAITING_FOR_UNBAN_ID';
        return bot.sendMessage(chatId, "🔓 আনব্যান করার জন্য ইউজারের **Telegram ID** দিন:");
    }

    // ৭. User Mode
    if (text === "🔙 User Mode" && chatId === ADMIN_ID) {
        delete userState[chatId];
        return bot.sendMessage(chatId, "🔄 **User Mode-এ সুইচ করা হয়েছে।**", userMenu);
    }

    // ==================== [ STATE PROCESSING ] ====================

    // Ban Processing
    if (userState[chatId] === 'WAITING_FOR_BAN_ID' && chatId === ADMIN_ID) {
        const targetId = parseInt(text);
        if (isNaN(targetId)) return bot.sendMessage(chatId, "❌ সঠিক সংখ্যা বা আইডি দিন!");
        bannedUsers.add(targetId);
        delete userState[chatId];
        return bot.sendMessage(chatId, `✅ ইউজার \`${targetId}\` কে সফলভাবে ব্যান করা হয়েছে।`, adminMenu);
    }

    // Unban Processing
    if (userState[chatId] === 'WAITING_FOR_UNBAN_ID' && chatId === ADMIN_ID) {
        const targetId = parseInt(text);
        if (isNaN(targetId)) return bot.sendMessage(chatId, "❌ সঠিক সংখ্যা বা আইডি দিন!");
        bannedUsers.delete(targetId);
        delete userState[chatId];
        return bot.sendMessage(chatId, `✅ ইউজার \`${targetId}\` কে সফলভাবে আনব্যান করা হয়েছে।`, adminMenu);
    }

    // Link Processing
    if (userState[chatId] === 'WAITING_FOR_LINK') {
        if (!text.startsWith('http://') && !text.startsWith('https://')) {
            return bot.sendMessage(chatId, "❌ অনুগ্রহ করে সঠিক URL দিন (https:// সহ)!");
        }

        const waitMsg = await bot.sendMessage(chatId, "⏳ ওয়েবসাইট থেকে HTML ডিকোড করা হচ্ছে...");
        try {
            const response = await axios.get(text, {
                headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' }
            });
            const cleanCode = processAndCleanHTML(response.data);

            const filePath = `./clean_source_${Date.now()}.html`;
            fs.writeFileSync(filePath, cleanCode);

            await bot.sendDocument(chatId, filePath, {
                caption: `✅ **সফলভাবে ডিকোড করা হয়েছে!**\n🔗 Source: ${text}`
            });

            fs.unlinkSync(filePath);
            bot.deleteMessage(chatId, waitMsg.message_id);
        } catch (err) {
            bot.sendMessage(chatId, "❌ লিংক থেকে ডাটা আনতে সমস্যা হয়েছে: " + err.message);
        }
        delete userState[chatId];
        return;
    }

    // Raw HTML Text Processing
    if (userState[chatId] === 'WAITING_FOR_HTML' && text && !msg.document) {
        const waitMsg = await bot.sendMessage(chatId, "⏳ HTML ডিকোড করা হচ্ছে...");
        try {
            const cleanCode = processAndCleanHTML(text);
            const filePath = `./clean_decoded_${Date.now()}.html`;
            fs.writeFileSync(filePath, cleanCode);

            await bot.sendDocument(chatId, filePath, {
                caption: "✅ **আপনার HTML সফলভাবে ডিকোড ও ক্লিন করা হয়েছে!**"
            });

            fs.unlinkSync(filePath);
            bot.deleteMessage(chatId, waitMsg.message_id);
        } catch (err) {
            bot.sendMessage(chatId, "❌ " + err.message);
        }
        delete userState[chatId];
        return;
    }
});

// HTML Document Processing
bot.on('document', async (msg) => {
    const chatId = msg.chat.id;
    if (bannedUsers.has(chatId)) return;

    if (userState[chatId] === 'WAITING_FOR_HTML' || !userState[chatId]) {
        const fileId = msg.document.file_id;
        const fileLink = await bot.getFileLink(fileId);

        const waitMsg = await bot.sendMessage(chatId, "⏳ ফাইল থেকে HTML ডাউনলোড ও ক্লিন করা হচ্ছে...");
        try {
            const response = await axios.get(fileLink);
            const cleanCode = processAndCleanHTML(response.data);

            const filePath = `./clean_file_${Date.now()}.html`;
            fs.writeFileSync(filePath, cleanCode);

            await bot.sendDocument(chatId, filePath, {
                caption: "✅ **আপনার HTML ফাইলটি ক্লিন করে নিচে দেওয়া হলো!**"
            });

            fs.unlinkSync(filePath);
            bot.deleteMessage(chatId, waitMsg.message_id);
        } catch (err) {
            bot.sendMessage(chatId, "❌ ফাইল ডিকোড করতে সমস্যা হয়েছে: " + err.message);
        }
        delete userState[chatId];
    }
});
