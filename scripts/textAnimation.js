import { randomDelay } from "./helpers.js";

const baseTypingSpeed = 80;
const baseWaitSpeed = 2000;
const CURSOR = "|";
export const HIDDEN_CURSOR = "\u00A0"; // NBSP


export function typeText(element, text, typingSpeed = baseTypingSpeed, waitSpeed = baseWaitSpeed) {
    return new Promise((resolve) => {
        let index = 0;
        let cursorVisible = true;

        const cursorTimer = setInterval(() => {
            cursorVisible = !cursorVisible;
            element.textContent =
                text.slice(0, index) + (cursorVisible ? CURSOR : HIDDEN_CURSOR);
        }, 500);

        element.textContent = "|";

        function nextLetter() {
            if (index < text.length) {
                index++;
                element.textContent =
                    text.slice(0, index) + (cursorVisible ? CURSOR : HIDDEN_CURSOR);
                setTimeout(nextLetter, randomDelay(typingSpeed));
            } else {
                clearInterval(cursorTimer);
                element.textContent = text;
                resolve();
            }
        }

        setTimeout(nextLetter, randomDelay(waitSpeed));
    });
}

export function eraseText(
    element,
    typingSpeed = baseTypingSpeed,
    waitSpeed = baseWaitSpeed,
    keepPlaceholder = false,
) {
    return new Promise((resolve) => {
        const text = element.textContent;
        let index = text.length;
        let cursorVisible = true;

        const cursorTimer = setInterval(() => {
            cursorVisible = !cursorVisible;
            element.textContent =
                text.slice(0, index) +
                (cursorVisible ? CURSOR : HIDDEN_CURSOR);
        }, 500);

        element.textContent = text + CURSOR;

        setTimeout(() => {
            function backspace() {
                if (index > 0) {
                    index--;
                    element.textContent =
                        text.slice(0, index) +
                        (cursorVisible ? CURSOR : HIDDEN_CURSOR);
                    setTimeout(backspace, randomDelay(typingSpeed));
                } else {
                    clearInterval(cursorTimer);

                    // Leave an invisible placeholder if requested.
                    element.textContent = keepPlaceholder
                        ? HIDDEN_CURSOR
                        : "";

                    resolve();
                }
            }

            backspace();
        }, randomDelay(waitSpeed));
    });
}