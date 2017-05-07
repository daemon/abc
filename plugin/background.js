const TITLE_APPLY = "Simplify English";
const TITLE_REMOVE = "Unsimplify English";
const APPLICABLE_PROTOCOLS = ["http:", "https:"];

function toggleSimplify(tab) {
  function gotTitle(title) {
    if (title === TITLE_APPLY) {
      browser.pageAction.setIcon({tabId: tab.id, path: "icons/on.png"});
      browser.pageAction.setTitle({tabId: tab.id, title: TITLE_REMOVE});
      browser.tabs.executeScript({ file: "jquery.min.js" }).then(function(r) {
        browser.tabs.executeScript({ file: "load-simplified.js" });
      });
    } else {
      browser.pageAction.setIcon({tabId: tab.id, path: "icons/off.png"});
      browser.pageAction.setTitle({tabId: tab.id, title: TITLE_APPLY});
      browser.tabs.executeScript({ file: "jquery.min.js" }).then(function(r) {
        browser.tabs.executeScript({ file: "unload-simplified.js" });
      });
    }
  }

  var gettingTitle = browser.pageAction.getTitle({tabId: tab.id});
  gettingTitle.then(gotTitle);
}

function protocolIsApplicable(url) {
  var anchor =  document.createElement('a');
  anchor.href = url;
  return APPLICABLE_PROTOCOLS.includes(anchor.protocol);
}

function initializePageAction(tab) {
  if (protocolIsApplicable(tab.url)) {
    browser.pageAction.setIcon({tabId: tab.id, path: "icons/off.png"});
    browser.pageAction.setTitle({tabId: tab.id, title: TITLE_APPLY});
    browser.pageAction.show(tab.id);
  }
}

var gettingAllTabs = browser.tabs.query({});
gettingAllTabs.then((tabs) => {
  for (tab of tabs) {
    initializePageAction(tab);
  }
});

browser.tabs.onUpdated.addListener((id, changeInfo, tab) => {
  initializePageAction(tab);
});
browser.pageAction.onClicked.addListener(toggleSimplify);
