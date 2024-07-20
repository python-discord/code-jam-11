import sys
import ecosystem

if __name__ == "__main__":

    if len(sys.argv) > 1 and sys.argv[1] == "--gifs":
        print("Running in GIF generation mode...")
        for gif_path, timestamp in ecosystem.run_gif_generator(duration=180):
            print(f"New GIF generated at {timestamp}: {gif_path}")
    else:
        print("Running in interactive mode...")
        ecosystem.run_pygame(show_controls=True, generate_gifs=False)
