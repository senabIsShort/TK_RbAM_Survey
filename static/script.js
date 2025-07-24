document.addEventListener("DOMContentLoaded", function () {
  const relationSelect = document.querySelector('select[name="predictedRelation"]');
  const relationDiv = document.querySelector(".relation");

  if (relationSelect && relationDiv) {
    relationSelect.addEventListener("change", function () {
      // Remove existing color classes
      relationDiv.classList.remove("support", "attack", "neutral");

      // Add the appropriate color class based on selection
      if (this.value) {
        relationDiv.classList.add(this.value);
      }
    });
  }

  // Burger menu functionality
  const burgerMenu = document.getElementById("burger-menu");
  const navLinks = document.getElementById("nav-links");

  if (burgerMenu && navLinks) {
    burgerMenu.addEventListener("click", function () {
      burgerMenu.classList.toggle("active");
      navLinks.classList.toggle("active");
    });

    // Close menu when clicking on a link
    const links = navLinks.querySelectorAll("a");
    links.forEach(link => {
      link.addEventListener("click", function () {
        burgerMenu.classList.remove("active");
        navLinks.classList.remove("active");
      });
    });

    // Close menu when clicking outside
    document.addEventListener("click", function (event) {
      if (!burgerMenu.contains(event.target) && !navLinks.contains(event.target)) {
        burgerMenu.classList.remove("active");
        navLinks.classList.remove("active");
      }
    });
  }
});
