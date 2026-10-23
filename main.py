const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');
const fs = require('fs');
const jsdom = require('jsdom');
const { JSDOM } = jsdom;

// ==================== [ CONFIGURATION ] ====================
const TOKEN = '8855372052:AAHJ04PSoc6nBSAP71upW0N6gdSmnNYkdz8';
const ADMIN_ID = 8419760844;
const DEVELOPER_HANDLE = '@NIROB_GX_LEADER';
const DEVELOPER_LINK = 'https://t.me/@NIROB_GX_LEADER';

const bot = new TelegramBot(TOKEN, { polling: true });

// ডাটাবেস ভেরিয়েবল
let bannedUsers = new Set();
let allUsers = new Set();
let userState = {};

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

// ==================== [ SMART HTML DECODING LOGIC ] ====================
function processAndCleanHTML(inputHtml) {
    try {
        // ১. শুধুমাত্র ক্ষতিকর সিকিউরিটি ট্র্যাপ রিমুভ করা (অ্যানিমেশন বা নরমাল JS ভাঙবে না)
        let cleanedText = inputHtml.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, (match) => {
            // শুধুমাত্র ধ্বংসাত্মক ও অ্যান্টি-ইনস্পেক্ট ট্র্যাপ স্ক্রিপ্ট রিমুভ
            if (
                match.includes('destroyAndRedirect') ||
                match.includes('speechSynthesis') ||
                match.includes('dense_junk_stream') ||
                match.includes('keyCode === 123') ||
                match.includes('debugger') ||
                match.includes('contextmenu')
            ) {
                return ''; // ক্ষতিকর স্ক্রিপ্ট বাদ
            }
            return match; // কাজের JS এবং অ্যানিমেশন কোড রেখে দেওয়া
        });

        // ২. JSDOM দিয়ে DOM তৈরি
        const dom = new JSDOM(cleanedText);
        const { document } = dom.window;

        // ৩. ক্ষতিকর ইভেন্ট লিসেনার স্ক্রিপ্ট ফিল্টার করা
        const scripts = document.querySelectorAll('script');
        scripts.forEach(script => {
            const code = script.textContent || '';
            if (
                code.includes('destroyAndRedirect') || 
                code.includes('speechSynthesis') || 
                code.includes('keyCode === 123')
            ) {
                script.remove();
            }
        });

        // ৪. ফাইনাল ডিকোডেড ক্লিন HTML আউটপুট
        let finalHtml = document.documentElement.outerHTML;
        if (!finalHtml.toLowerCase().startsWith('<!doctype')) {
            finalHtml = '<!DOCTYPE html>\n' + finalHtml;
        }

        return finalHtml;
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
        return bot.sendMessage(chatId, "❌ *আপনি এই বট থেকে ব্যান হয়ে আছেন!*", { parse_mode: 'Markdown' });
    }

    if (chatId === ADMIN_ID) {
        bot.sendMessage(chatId, `👑 *Welcome Admin!*\n\nআপনি অ্যাডমিন প্যানেলে আছেন। আপনার কন্ট্রোল বাটন নিচে দেওয়া হলো:`, { ...adminMenu, parse_mode: 'Markdown' });
    } else {
        bot.sendMessage(chatId, `👋 *Welcome to GX HTML Decoder Bot!*\n\nনিচের বাটনগুলো ব্যবহার করে আপনার অপশন সিলেক্ট করুন:`, { ...userMenu, parse_mode: 'Markdown' });
    }
});

// /admin কমান্ড
bot.onText(/\/admin/, (msg) => {
    if (msg.chat.id !== ADMIN_ID) return;
    bot.sendMessage(msg.chat.id, "🛠 *Admin Panel Loaded!*", { ...adminMenu, parse_mode: 'Markdown' });
});

// মেসেজ হ্যান্ডলিং
bot.on('message', async (msg) => {
    const chatId = msg.chat.id;
    const text = msg.text ? msg.text.trim() : '';

    if (bannedUsers.has(chatId)) return;
    allUsers.add(chatId);

    // ১. Developer Info (ফিক্সড ইউজারনেম ও সোজা লিংক)
    if (text === "👨‍💻 Developer Info") {
        const devMsg = `💻 *Developer Details*\n\n` +
                       `👤 *Developer:* @NIROB_GX_LEADER (${DEVELOPER_HANDLE})\n` +
                       `🔗 *Telegram Direct:* https://t.me/NIROB\\_GX\\_LEADER\n` +
                       `🛡 *Powered By:* GX BIG COMMUNITY\n\n` +
                       `যেকোনো প্রয়োজনে সরাসরি যোগাযোগ করতে পারেন:\n` +
                       `👉 ${DEVELOPER_LINK}`;
                       
        return bot.sendMessage(chatId, devMsg, { 
            parse_mode: 'Markdown',
            disable_web_page_preview: true 
        });
    }

    // ২. HTML to Decode
    if (text === "📜 HTML to Decode") {
        userState[chatId] = 'WAITING_FOR_HTML';
        return bot.sendMessage(chatId, "📥 *আপনার Obfuscated / Encrypted HTML কোডটি এখানে পেস্ট করুন অথবা HTML ফাইল পাঠিয়া দিন:*", { parse_mode: 'Markdown' });
    }

    // ৩. Link to Decode
    if (text === "🔗 Link to Decode") {
        userState[chatId] = 'WAITING_FOR_LINK';
        return bot.sendMessage(chatId, "🌐 *যে ওয়েবসাইট বা লিংকের HTML ডিকোড করতে চান, তার URL টি দিন:*\n*(যেমন: https://example.com)*", { parse_mode: 'Markdown' });
    }

    // ৪. অ্যাডমিন: All Users
    if (text === "📊 All Users" && chatId === ADMIN_ID) {
        let userList = `👥 *মোট ইউজার সংখ্যা (${allUsers.size}):*\n\n`;
        allUsers.forEach(id => {
            userList += `• \`${id}\` ${bannedUsers.has(id) ? '❌ (Banned)' : '✅'}\n`;
        });
        return bot.sendMessage(chatId, userList, { parse_mode: 'Markdown' });
    }

    // ৫. অ্যাডমিন: Ban User
    if (text === "🚫 Ban User" && chatId === ADMIN_ID) {
        userState[chatId] = 'WAITING_FOR_BAN_ID';
        return bot.sendMessage(chatId, "⚠️ ব্যান করার জন্য ইউজারের *Telegram ID* দিন:", { parse_mode: 'Markdown' });
    }

    // ৬. অ্যাডমিন: Unban User
    if (text === "✅ Unban User" && chatId === ADMIN_ID) {
        userState[chatId] = 'WAITING_FOR_UNBAN_ID';
        return bot.sendMessage(chatId, "🔓 আনব্যান করার জন্য ইউজারের *Telegram ID* দিন:", { parse_mode: 'Markdown' });
    }

    // ৭. User Mode
    if (text === "🔙 User Mode" && chatId === ADMIN_ID) {
        delete userState[chatId];
        return bot.sendMessage(chatId, "🔄 *User Mode-এ সুইচ করা হয়েছে।*", { ...userMenu, parse_mode: 'Markdown' });
    }

    // ==================== [ STATE PROCESSING ] ====================

    if (userState[chatId] === 'WAITING_FOR_BAN_ID' && chatId === ADMIN_ID) {
        const targetId = parseInt(text);
        if (isNaN(targetId)) return bot.sendMessage(chatId, "❌ সঠিক সংখ্যা বা আইডি দিন!");
        bannedUsers.add(targetId);
        delete userState[chatId];
        return bot.sendMessage(chatId, `✅ ইউজার \`${targetId}\` কে সফলভাবে ব্যান করা হয়েছে।`, { ...adminMenu, parse_mode: 'Markdown' });
    }

    if (userState[chatId] === 'WAITING_FOR_UNBAN_ID' && chatId === ADMIN_ID) {
        const targetId = parseInt(text);
        if (isNaN(targetId)) return bot.sendMessage(chatId, "❌ সঠিক সংখ্যা বা আইডি দিন!");
        bannedUsers.delete(targetId);
        delete userState[chatId];
        return bot.sendMessage(chatId, `✅ ইউজার \`${targetId}\` কে সফলভাবে আনব্যান করা হয়েছে।`, { ...adminMenu, parse_mode: 'Markdown' });
    }

    // Link Processing
    if (userState[chatId] === 'WAITING_FOR_LINK') {
        if (!text.startsWith('http://') && !text.startsWith('https://')) {
            return bot.sendMessage(chatId, "❌ অনুগ্রহ করে সঠিক URL দিন (https:// সহ)!");
        }

        const waitMsg = await bot.sendMessage(chatId, "⏳ ওয়েবসাইট থেকে রিয়েল অ্যানিমেটেড HTML ডিকোড ও ক্লিন করা হচ্ছে...");
        try {
            const response = await axios.get(text, {
                headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' }
            });
            const cleanCode = processAndCleanHTML(response.data);

            const filePath = `./clean_source_${Date.now()}.html`;
            fs.writeFileSync(filePath, cleanCode);

            await bot.sendDocument(chatId, filePath, {
                caption: `✅ *সফলভাবে ডিকোড করা হয়েছে (অ্যানিমেশন সহ রানিং)!*\n🔗 Source: ${text}`,
                parse_mode: 'Markdown'
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
        const waitMsg = await bot.sendMessage(chatId, "⏳ HTML ডিকোড ও ক্লিন করা হচ্ছে...");
        try {
            const cleanCode = processAndCleanHTML(text);
            const filePath = `./clean_decoded_${Date.now()}.html`;
            fs.writeFileSync(filePath, cleanCode);

            await bot.sendDocument(chatId, filePath, {
                caption: "✅ *আপনার HTML সফলভাবে ডিকোড করা হয়েছে! (সব অ্যানিমেশন ও ইন্টারঅ্যাকশন ১০০% কাজ করবে)*",
                parse_mode: 'Markdown'
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

        const waitMsg = await bot.sendMessage(chatId, "⏳ ফাইল থেকে HTML ডিকোড ও প্রসেস করা হচ্ছে...");
        try {
            const response = await axios.get(fileLink);
            const cleanCode = processAndCleanHTML(response.data);

            const filePath = `./clean_file_${Date.now()}.html`;
            fs.writeFileSync(filePath, cleanCode);

            await bot.sendDocument(chatId, filePath, {
                caption: "✅ *আপনার HTML ফাইলটি প্রপার অ্যানিমেশন সহ ক্লিন করে নিচে পাঠানো হলো!*",
                parse_mode: 'Markdown'
            });

            fs.unlinkSync(filePath);
            bot.deleteMessage(chatId, waitMsg.message_id);
        } catch (err) {
            bot.sendMessage(chatId, "❌ ফাইল ডিকোড করতে সমস্যা হয়েছে: " + err.message);
        }
        delete userState[chatId];
    }
});
