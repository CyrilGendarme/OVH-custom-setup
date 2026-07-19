import { WebSocketService } from "./websocketClientService.js";

export function initWordDisplay(selector) {
    let finalWord = "";
    const frameDelay = 140;
    const randomUnderscoreChance = 0.45;
    const clearAfterMs = 7500;

    const element = document.querySelector(selector);

    if (!element) {
        console.error(`Element not found: ${selector}`);
        return;
    }

    function getGeometry() {
        return {
            len: finalWord.length,
            center: (finalWord.length - 1) / 2,
        };
    }

    let radius = 0;
    let solved = [];
    let clearTimer = null;

    function scheduleClear() {
        if (clearTimer) {
            clearTimeout(clearTimer);
        }

        clearTimer = setTimeout(() => {
            element.textContent = "";
            finalWord = "";
            solved = [];
            radius = 0;
            clearTimer = null;
        }, clearAfterMs);
    }

    function resetAnimation(newWord) {
        finalWord = newWord.toUpperCase();
        radius = 0;
        solved = new Array(finalWord.length).fill(false);
        element.textContent = "";
        scheduleClear();
        step();
    }

    function render() {
        const geometry = getGeometry();

        let output = "";

        for (let i = 0; i < geometry.len; i++) {
            const dist = Math.abs(i - geometry.center);

            if (dist > radius) {
                output += " ";
                continue;
            }

            if (solved[i]) {
                output += finalWord[i];
            } else {
                if (Math.random() < randomUnderscoreChance) {
                    solved[i] = true;
                    output += finalWord[i];
                } else {
                    output += "_";
                }
            }
        }

        element.textContent = output;
    }

    function step() {
        render();

        radius += 0.45;

        if (solved.every((v) => v)) {
            element.textContent = finalWord;
            return;
        }

        const delay = Math.max(
            Math.min((frameDelay / finalWord.length) * 12, frameDelay),
            frameDelay / 2,
        );

        setTimeout(step, delay);
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

        const title =
            typeof data.title === "string" ? data.title.trim() : "";

        if (artist && title) {
            return `${artist} - ${title}`;
        }

        return title || artist || "";
    }

    function handleIncomingMessage(event) {
        let data = event.data;

        if (typeof event.data === "string") {
            try {
                data = JSON.parse(event.data);
            } catch {
                data = event.data;
            }
        }

        const text = getDisplayText(data);

        if (text) {
            resetAnimation(text);
        }
    }

    window.obsTrigger = resetAnimation;

    const socket = new WebSocketService({
        port: 8765,
        onMessage: handleIncomingMessage,
    });

    socket.connect();

    // optional initial animation
    step();
}