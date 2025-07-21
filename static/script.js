document.addEventListener("DOMContentLoaded", function () {
  const relationSelect = document.querySelector('select[name="relation"]');
  const relationDiv = document.querySelector(".relation");

  relationSelect.addEventListener("change", function () {
    // Remove existing color classes
    relationDiv.classList.remove("support", "attack", "neutral");

    // Add the appropriate color class based on selection
    if (this.value) {
      relationDiv.classList.add(this.value);
    }
  });
});
