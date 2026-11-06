document.getElementById("generateForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const count = document.querySelector("input[name='count']").value;
    const response = await fetch("/generate", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body:nt-Type": "applica    });
    const results = await response.json();
    document.getElementById("results").innerText = results.map(r =>
        ${r.status}: ${r.email} | ${r.password}
    ).join("\n");
});
