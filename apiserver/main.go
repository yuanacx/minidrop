package main

import (
	"log"
	"os"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/minidrop/apiserver/internal/dropclient"
	"github.com/minidrop/apiserver/internal/handlers"
	"github.com/minidrop/apiserver/internal/models"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

func main() {
	dsn := os.Getenv("PG_DSN")
	if dsn == "" {
		dsn = "host=postgres user=postgres password=dev dbname=drop sslmode=disable"
	}
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		log.Fatal(err)
	}
	if err := migrateDB(db); err != nil {
		log.Fatal(err)
	}

	r := gin.Default()
	origin := os.Getenv("CORS_ORIGIN")
	if origin == "" {
		origin = "http://localhost"
	}
	r.Use(cors.New(cors.Config{
		AllowOrigins:     []string{origin},
		AllowCredentials: true,
		AllowMethods:     []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowHeaders:     []string{"Origin", "Content-Type", "Accept"},
	}))

	api := &handlers.API{DB: db, Drop: dropclient.New()}
	api.Register(r)

	addr := ":8191"
	log.Printf("apiserver listening %s", addr)
	if err := r.Run(addr); err != nil {
		log.Fatal(err)
	}
}

func migrateDB(db *gorm.DB) error {
	return db.AutoMigrate(&models.Task{}, &models.TaskStatusHistory{}, &models.AgentAudit{})
}
