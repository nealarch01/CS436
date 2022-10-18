package main

import (
	"fmt"
	"io"
	http "net/http"
	"sync"
	"time"
)

func printBody(responseBody *io.ReadCloser) {
	body, err := io.ReadAll(*responseBody) // De-reference the pointer to the response body
	if err != nil {
		fmt.Println("Error reading body. ", err)
		return
	}
	fmt.Println("Response Body:\n", string(body))
}

func httpRequest(url string, waitGroup *sync.WaitGroup, pid int) {
	defer waitGroup.Done() //
	response, err := http.Get(url)
	if err != nil {
		fmt.Println("PID:", pid, "No response from server.")
		return
	}
	time := time.Now().UnixMicro()
	fmt.Println("PID:", pid, "Current time of connection:", time)
	fmt.Println("PID:", pid, "Response Status:", response.Status)
	// printBody(&response.Body)
}

func concurrentRequest() {
	var waitGroup sync.WaitGroup
	url1 := "http://127.0.0.1:6789/"
	waitGroup.Add(2) // Create a wait group with 3 goroutines
	go httpRequest(url1, &waitGroup, 1)
	// Purpose of sleep is to make sure that the backlog queue has processed the initial request, 
	// Without the delay, the second request will be rejected because of the full backlog.
	// Note: This varies depending on the machine, my socket initialization took on average, 0.67 milliseconds.
	time.Sleep(1000 * time.Microsecond) // Sleep to 1 millisecond / 1000 microseconds
	go httpRequest(url1, &waitGroup, 2)
	waitGroup.Wait() // Wait for the responses to complete before returning to the main function.
}

func main() {
	concurrentRequest()
}
