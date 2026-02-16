from bot import iniciar_bot

if __name__ == "__main__":
    try:
        while True:
            iniciar_bot()
    except KeyboardInterrupt:
        print("\n🛑 Programa finalizado por el usuario.")