function createSocialItems(items) {
    return items
        .map(({ icon, name }) => `
            <div class="social">
                ${icon ? `<i class="${icon}"></i>` : ""}
                <span class="social-name">${name}</span>
            </div>
        `)
        .join("");
}


function createMarqueeTrack(direction, items, offset = 0) {
    const copies = direction === "left" ? 2 : 3;

    const track = document.createElement("div");
    track.className = `marquee-track marquee-${direction} ${direction}`;
    track.style.marginLeft = `${offset}px`;

    track.innerHTML = Array.from(
        { length: copies },
        () => `
            <div class="marquee-content">
                ${createSocialItems(items)}
            </div>
        `
    ).join("");

    return track;
}


function buildMarquee(
    container,
    itemsLeft,
    itemsRight,
    rows,
    offsets = []
) {
    if (typeof container === "string") {
        container = document.getElementById(container);
    }

    if (!container) {
        throw new Error("Marquee container not found.");
    }

    container.innerHTML = "";

    for (let i = 0; i < rows; i++) {
        const direction = i % 2 === 0 ? "left" : "right";

        container.appendChild(
            createMarqueeTrack(
                direction,
                direction === "left" ? itemsLeft : itemsRight,
                offsets[i] ?? 0
            )
        );
    }
}