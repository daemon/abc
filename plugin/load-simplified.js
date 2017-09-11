var getTextNodesIn = function(el) {
    return $(el).find(":not(iframe)").addBack().contents().filter(function() {
        return this.nodeType == 3;
    });
};

var nodes = getTextNodesIn("body");
window.translations = {}
var i = 0;
for (var n of nodes) {
  window.translations[i] = n.textContent;
  (function (n) {
    fetch("http://127.0.0.1:16384/simplify", {
      method: "POST",
      mode: "cors",
      body: JSON.stringify({text: n.textContent})
    }).then(function(response) {
      if(response.ok) {
        response.json().then(function(json) {
          n.textContent = json["text"];
        });
      } else {
        console.log('Network response was not ok.');
      }
    })
    .catch(function(error) {
      console.log('There has been a problem with your fetch operation: ' + error.message);
    });
  }).call(this, n);
  i += 1;
}