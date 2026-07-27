import { sleep, randomDelay, normalizeIncomingTrackEvent } from "./helpers.js";
import { typeText, eraseText } from "./textAnimation.js";

export function createTracklist({ container, maxItems = 8 }) {
    if (typeof container === "string") {
        container = document.getElementById(container);
    }

    if (!container) {
        throw new Error("Tracklist container not found");
    }

    const trackItems = [];
    const baseSpeed = 80;
    const randomness = 0.2;
    let animationQueue = Promise.resolve();

    function createTrackElement(text = "") {
        const div = document.createElement("div");
        div.className = "tracklist-item";
        const span = document.createElement("span");
        div.appendChild(span);
        container.prepend(div);

        return {
            div,
            span,
            text,
        };
    }

    async function addTrack(text) {
        if (trackItems.length >= maxItems) {
            const oldest = trackItems.pop();
            await eraseText(oldest.span);
            oldest.div.remove();
            await sleep(randomDelay(baseSpeed));
        }

        const item = createTrackElement(text);
        trackItems.unshift(item);
        await typeText(item.span, text);
    }

    function queueTrack(text) {
        if (!text) {
            return;
        }
        animationQueue = animationQueue.then(() => addTrack(text));
    }

    function getDisplayText(data) {
        if (typeof data === "string" && data.trim()) {
            return data.trim();
        }

        if (!data || typeof data !== "object") {
            return "";
        }

        if (typeof data.text === "string" && data.text.trim()) {
            return data.text.trim();
        }

        if (typeof data.message === "string" && data.message.trim()) {
            return data.message.trim();
        }

        const artist =
            typeof data.artist === "string" ? data.artist.trim() : "";

        const title = typeof data.title === "string" ? data.title.trim() : "";

        if (artist && title) {
            return `${artist} - ${title}`;
        }

        return title || artist || "";
    }

    function handleMessage(data) {
        const normalizedData = normalizeIncomingTrackEvent(data);
        if (!normalizedData) {
            return;
        }

        const text = getDisplayText(normalizedData);

        if (text) {
            queueTrack(text);
        }
    }

    return {
        add: queueTrack,
        handleMessage,
    };
}
