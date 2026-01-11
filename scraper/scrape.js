const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const PROFILE_PATH = path.join(__dirname, 'chrome_profile');
const OUTPUT_FILE = path.join(__dirname, '../frontend/public/bookmarks_clean.json');

if (!fs.existsSync(path.dirname(OUTPUT_FILE))) {
    fs.mkdirSync(path.dirname(OUTPUT_FILE), { recursive: true });
}

(async () => {
    console.log('Launching browser...');
    const browserContext = await chromium.launchPersistentContext(PROFILE_PATH, {
        headless: false,
        viewport: { width: 1280, height: 720 },
        args: ['--disable-blink-features=AutomationControlled']
    });

    const page = await browserContext.newPage();
    const bookmarks = new Map();

    if (fs.existsSync(OUTPUT_FILE)) {
        try {
            const existing = JSON.parse(fs.readFileSync(OUTPUT_FILE));
            existing.forEach(b => bookmarks.set(b.id, b));
            console.log(`Loaded ${bookmarks.size} existing bookmarks.`);
        } catch (e) { }
    }

    page.on('response', async (response) => {
        const url = response.url();
        if (url.includes('graphql') && (url.includes('Bookmark') || url.includes('Bookmarks'))) {
            try {
                const json = await response.json();
                processBookmarks(json, bookmarks);
            } catch (e) {
                // ignore
            }
        }
    });

    console.log('Navigating to bookmarks...');
    await page.goto('https://twitter.com/i/bookmarks', { waitUntil: 'domcontentloaded' });

    console.log('\n=== INSTRUCTIONS ===');
    console.log('1. Log in to X/Twitter if not already logged in.');
    console.log('2. The script will wait 15 seconds to start auto-scrolling.');
    console.log('3. Interrupt manually (Ctrl+C) to stop and save.');
    console.log('====================\n');

    await page.waitForTimeout(15000);

    console.log('Starting scroll loop... Press Ctrl+C to stop.');

    let noNewCount = 0;
    let lastSize = bookmarks.size;

    let keepRunning = true;

    process.on('SIGINT', async () => {
        if (!keepRunning) return;
        keepRunning = false;
        console.log('\nStopping...');
        try {
            await saveBookmarks(bookmarks);
            await browserContext.close();
        } catch (e) {
            // ignore
        }
        process.exit(0);
    });

    while (keepRunning) {
        try {
            await page.evaluate(() => window.scrollBy(0, 1000));
            await page.waitForTimeout(2000);
        } catch (e) {
            if (!keepRunning) break;
            console.error('Error during scroll:', e.message);
            break;
        }

        if (bookmarks.size > lastSize) {
            process.stdout.write(`\rCollected ${bookmarks.size} bookmarks (+${bookmarks.size - lastSize})`);
            lastSize = bookmarks.size;
            noNewCount = 0;
        } else {
            noNewCount++;
            process.stdout.write(`\rCollected ${bookmarks.size} bookmarks (no new items: ${noNewCount})`);
        }

        if (bookmarks.size % 50 === 0) {
            saveBookmarks(bookmarks, false);
        }
    }
})();

function processBookmarks(json, map) {
    const instructions = json?.data?.bookmark_timeline_v2?.timeline?.instructions || [];
    for (const instruction of instructions) {
        if (instruction.type === 'TimelineAddEntries') {
            for (const entry of instruction.entries) {
                const tweetResult = entry.content?.itemContent?.tweet_results?.result;
                if (tweetResult) {
                    extractTweet(tweetResult, map);
                }
            }
        }
    }
}

function extractTweet(data, map) {
    const result = data.tweet || data;
    if (!result.legacy) return;

    const id = result.rest_id;
    const legacy = result.legacy;
    const user = result.core?.user_results?.result?.legacy?.screen_name || 'unknown';
    const text = legacy.full_text || '';
    const timestamp = legacy.created_at;

    const media = [];
    let videoUrl = null;

    if (legacy.entities && legacy.entities.media) {
        for (const m of legacy.entities.media) {
            media.push(m.media_url_https);
        }
    }

    if (legacy.extended_entities && legacy.extended_entities.media) {
        for (const m of legacy.extended_entities.media) {
            if (m.type === 'video' || m.type === 'animated_gif') {
                const variants = m.video_info?.variants || [];
                const best = variants
                    .filter(v => v.content_type === 'video/mp4')
                    .sort((a, b) => (b.bitrate || 0) - (a.bitrate || 0))[0];
                if (best) videoUrl = best.url;
            }
        }
    }

    map.set(id, {
        id,
        user,
        text,
        images: media,
        video: videoUrl,
        created_at: timestamp
    });
}

function saveBookmarks(map, log = true) {
    const arr = Array.from(map.values());
    fs.writeFileSync(OUTPUT_FILE, JSON.stringify(arr, null, 2));
    if (log) console.log(`\nSaved ${arr.length} bookmarks to ${OUTPUT_FILE}`);
}
