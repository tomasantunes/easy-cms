function toggleMenu() {
    var x = document.getElementById("top-nav1");
    if (x.className === "top-nav") {
        x.className += " responsive";
    } else {
        x.className = "top-nav";
    }
}

$.post("/increment-view", {page: window.location.pathname});