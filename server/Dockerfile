# Stage 1: Build the Go binary
FROM golang:1.24 AS builder

# Set the Current Working Directory inside the container
WORKDIR /app

# Copy go.mod and go.sum files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy the source code
COPY . .

# Build the Go app
RUN go build -o server ./cmd/server

# Stage 2: Create a minimal runtime image
FROM debian:bookworm-slim

# Set environment variables
ENV TZ=Asia/Jakarta \
    LANG=C.UTF-8

# Install certificates and time zone data
RUN apt-get update && \
    apt-get install -y ca-certificates tzdata && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory in runtime container
WORKDIR /app

# Copy the binary from builder
COPY --from=builder /app/server .
COPY --from=builder /app/.env .env

# Command to run the executable
CMD ["./server"]
