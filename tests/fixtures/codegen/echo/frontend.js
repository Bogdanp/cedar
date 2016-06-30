console.log("READY");
XMLHttpRequest = require("xmlhttprequest").XMLHttpRequest;

var app = require("./elm").Main.worker();

app.ports.respond.subscribe(function(res) {
  res.messages.forEach(function(message) {
    console.log(message);
  });

  if (!res.success) {
    process.exit(1);
  }
});
