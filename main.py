from time import sleep
from bot import iniciar_bot
from materias_store import cargar_materias, materias_pendientes

if __name__ == "__main__":
    try:
        materias = cargar_materias()
        if len(materias_pendientes(materias)) == 0:
            print("🎉 Todas las materias ya están marcadas como inscritas en materias.json.")
            print("Si deseas volver a inscribir, edita materias.json y coloca 'inscrita': false.")
            raise SystemExit(0)

        while True:
            exito = iniciar_bot()
            if exito:
                print("\n✅ Proceso completado: Todas las materias fueron inscritas con éxito.")
                break
            
            # Si hubo un fallo inesperado del navegador, reintentar tras una breve pausa
            materias_actuales = cargar_materias()
            if len(materias_pendientes(materias_actuales)) == 0:
                print("\n✅ No quedan materias pendientes por inscribir.")
                break

            print("\n🔄 Reiniciando bot en 3 segundos...")
            sleep(3)

    except KeyboardInterrupt:
        print("\n🛑 Programa finalizado por el usuario.")