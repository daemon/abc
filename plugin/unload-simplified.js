var getTextNodesIn = function(el) {
    return $(el).find(":not(iframe)").addBack().contents().filter(function() {
        return this.nodeType == 3;
    });
};

var nodes = getTextNodesIn("body");
var i = 0;
for (var n of nodes) {
  n.textContent = window.translations[i];
  i += 1;
}