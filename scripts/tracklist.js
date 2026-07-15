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

    function sleep(ms) {
        return new Promise((resolve) => setTimeout(resolve, ms));
    }

    function randomDelay(base = baseSpeed) {
        const variation = base * randomness;

        return base + (Math.random() * variation * 2 - variation);
    }

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

    function typeText(item) {
        return new Promise((resolve) => {
            const text = item.text;
            let index = 0;
            let cursorVisible = true;
            const cursorTimer = setInterval(() => {
                cursorVisible = !cursorVisible;

                item.span.textContent =
                    text.slice(0, index) + (cursorVisible ? "|" : "");
            }, 500);
            item.span.textContent = "|";

            function nextLetter() {
                if (index < text.length) {
                    index++;
                    item.span.textContent =
                        text.slice(0, index) + (cursorVisible ? "|" : "");
                    setTimeout(nextLetter, randomDelay());
                } else {
                    clearInterval(cursorTimer);
                    item.span.textContent = text;
                    resolve();
                }
            }

            setTimeout(nextLetter, randomDelay(2000));
        });
    }

    function eraseText(item) {
        return new Promise((resolve) => {
            const text = item.text;
            let index = text.length;
            let cursorVisible = true;
            const cursorTimer = setInterval(() => {
                cursorVisible = !cursorVisible;
                item.span.textContent =
                    text.slice(0, index) + (cursorVisible ? "|" : "");
            }, 500);

            item.span.textContent = text + "|";
            setTimeout(() => {
                function backspace() {
                    if (index > 0) {
                        index--;
                        item.span.textContent =
                            text.slice(0, index) + (cursorVisible ? "|" : "");
                        setTimeout(backspace, randomDelay());
                    } else {
                        clearInterval(cursorTimer);
                        item.div.remove();
                        resolve();
                    }
                }

                backspace();
            }, randomDelay(2000));
        });
    }

    async function addTrack(text) {
        if (trackItems.length >= maxItems) {
            const oldest = trackItems.pop();
            await eraseText(oldest);
            await sleep(randomDelay(1600));
        }

        const item = createTrackElement(text);
        trackItems.unshift(item);
        await typeText(item);
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
        if (typeof data === "string") {
            try {
                data = JSON.parse(data);
            } catch {}
        }

        const text = getDisplayText(data);

        if (text) {
            queueTrack(text);
        }
    }

    return {
        add: queueTrack,
        handleMessage,
    };
}
