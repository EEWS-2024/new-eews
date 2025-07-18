package app

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	sq "github.com/Masterminds/squirrel"
	"github.com/confluentinc/confluent-kafka-go/v2/kafka"
	"io"
	"net/http"
	"server/internal/config"
	"server/internal/domain"
	stationPort "server/internal/port/station"
	streamPort "server/internal/port/stream"
	"time"
)

type StreamService struct {
	stationRepo stationPort.StationRepository
	streamRepo  streamPort.StreamRepository
}

func NewStreamService(stationRepo stationPort.StationRepository, streamRepo streamPort.StreamRepository) *StreamService {
	return &StreamService{
		stationRepo: stationRepo,
		streamRepo:  streamRepo,
	}
}

func (s *StreamService) StartStream(ctx context.Context, spec domain.StartStreamPayload, cfg *config.Config) (err error) {
	stations, err := s.stationRepo.GetBy(ctx, sq.Eq{
		"is_enabled": true,
	})
	if err != nil {
		return err
	}

	stationCodes := make([]string, 0)
	for _, station := range stations {
		stationCodes = append(stationCodes, station.Code)
	}

	var payload []byte
	var url string
	if spec.StreamType == "LIVE" {
		url = fmt.Sprintf("%s/run", cfg.LiveUrl)
		payload, err = json.Marshal(map[string]any{
			"stations":   stationCodes,
			"model_type": spec.ModelType,
		})
	}

	if spec.StreamType == "ARCHIVE" {
		url = fmt.Sprintf("%s/run", cfg.ArchiveUrl)
		payload, err = json.Marshal(map[string]any{
			"stations":   stationCodes,
			"start_time": spec.StartTime.Format("2006-01-02T15:04:05"),
			"end_time":   spec.EndTime.Format("2006-01-02T15:04:05"),
			"model_type": spec.ModelType,
		})
	}

	var resp *http.Response
	if resp, err = http.Post(url, "application/json", bytes.NewBuffer(payload)); err != nil {
		return err
	}
	defer resp.Body.Close()

	var body []byte
	if body, err = io.ReadAll(resp.Body); err != nil {
		return err
	}

	var bodyResponse map[string]string
	if err = json.Unmarshal(body, &bodyResponse); err != nil {
		return err
	}

	if bodyResponse["status"] != "success" {
		return errors.New("stream client error")
	}

	if err = s.streamRepo.Create(
		ctx,
		"STARTED",
		spec.StreamType,
	); err != nil {
		return err
	}

	return nil
}

func (s *StreamService) StopStream(ctx context.Context, spec domain.StopStreamPayload, cfg *config.Config) (err error) {
	var baseUrl string
	if spec.StreamType == "LIVE" {
		baseUrl = cfg.LiveUrl
	}

	if spec.StreamType == "ARCHIVE" {
		baseUrl = cfg.ArchiveUrl
	}

	var payload []byte
	payload, err = json.Marshal(map[string]any{})

	var resp *http.Response
	if resp, err = http.Post(fmt.Sprintf("%s/stop", baseUrl), "application/json", bytes.NewBuffer(payload)); err != nil {
		return err
	}
	defer resp.Body.Close()

	var body []byte
	if body, err = io.ReadAll(resp.Body); err != nil {
		return err
	}

	var bodyResponse map[string]string
	if err = json.Unmarshal(body, &bodyResponse); err != nil {
		return err
	}

	if bodyResponse["status"] != "success" {
		return errors.New("stream client error")
	}

	if err = s.truncateKafka(cfg); err != nil {
		return err
	}

	if err = s.streamRepo.Update(
		ctx,
		map[string]any{
			"status":      "STOPPED",
			"finished_at": time.Now(),
		},
		"STARTED",
		spec.StreamType,
	); err != nil {
		return err
	}

	return nil
}

func (s *StreamService) truncateKafka(cfg *config.Config) (err error) {
	var admin *kafka.AdminClient
	admin, err = kafka.NewAdminClient(&kafka.ConfigMap{
		"bootstrap.servers": cfg.KafkaBootstrapServers,
	})
	if err != nil {
		panic(fmt.Sprintf("Failed to create AdminClient: %s", err))
	}
	defer admin.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err = s.DeleteTopic("trace", ctx, admin); err != nil {
		return
	}

	if err = s.DeleteTopic("predicted", ctx, admin); err != nil {
		return
	}

	return
}

func (s *StreamService) DeleteTopic(topic string, ctx context.Context, admin *kafka.AdminClient) error {
	results, err := admin.DeleteTopics(
		ctx,
		[]string{topic},
		kafka.SetAdminOperationTimeout(5*time.Second),
	)
	if err != nil {
		panic(fmt.Sprintf("DeleteTopics failed: %s", err))
	}

	for _, result := range results {
		if result.Error.Code() != kafka.ErrNoError {
			fmt.Printf("Failed to delete topic %s: %v\n", result.Topic, result.Error)
		} else {
			fmt.Printf("Topic %s deleted successfully.\n", result.Topic)
		}
	}

	return nil
}

func (s *StreamService) GetStream(ctx context.Context) (result map[string]bool, err error) {
	var streams []domain.Stream

	if streams, err = s.streamRepo.GetBy(ctx, sq.Eq{
		"status": "STARTED",
	}); err != nil {
		return nil, err
	}

	result = map[string]bool{
		"LIVE":    false,
		"ARCHIVE": false,
	}

	for _, stream := range streams {
		if ok := result[stream.StreamType]; !ok {
			result[stream.StreamType] = true
		}
	}

	return result, nil
}
