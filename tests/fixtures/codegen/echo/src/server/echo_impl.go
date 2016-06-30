package server

import "net/http"

// EchoImpl is an implementation of the Echo service.
var EchoImpl Echo

func init() {
	EchoImpl = Echo{}
	EchoImpl.HandleEcho(func(req *http.Request, data *EchoRequest) (string, error) {
		return data.Message, nil
	})
}
