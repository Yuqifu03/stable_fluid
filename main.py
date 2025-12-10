import argparse
import sys
import taichi as ti
from src.scenarios import SCENARIO_MAP
ti.init(arch=ti.gpu)

# ==============================
# Save GIF
# ==============================
def save_gif(frames, filename, fps=30):
    if not frames:
        print("Error: No frames generated.")
        return
    
    print(f"Saving to {filename} ({len(frames)} frames)...")
    frames[0].save(
        filename,
        save_all=True,
        append_images=frames[1:],
        duration=1000/fps,
        loop=0
    )
    print(f"Done! File saved: {filename}")


# ==============================
# GUI MODE SIMULATION
# ==============================
def run_gui(scenario_class):
    ti.init(arch=ti.cuda, debug=False)

    scenario = scenario_class()
    window = ti.ui.Window("Taichi Simulation", (800, 800))
    canvas = window.get_canvas()
    scene = ti.ui.Scene()
    camera = ti.ui.Camera()

    camera.position(0.5, 0.5, 2.0)
    camera.lookat(0.5, 0.5, 0.5)
    scene.set_camera(camera)

    while window.running:
        scenario.step()

        camera.track_user_inputs(
            window, movement_speed=0.1, hold_key=ti.ui.RMB
        )
        scene.set_camera(camera)

        scene.point_light((0, 5, 2), (1, 1, 1))
        scene.particles(
            scenario.particles,
            radius=scenario.particle_radius,
            per_vertex_color=scenario.particle_colors,
            index_count=scenario.pn_current
        )

        canvas.scene(scene)
        window.show()


def run_render(ScenarioClass, frames_count):
    try:
        if 'SCENARIO_MAP' in globals() and ScenarioClass is SCENARIO_MAP.get('starry_water'):
            scenario = ScenarioClass(duration=frames_count)
            frames = scenario.step()
            save_gif(frames, ScenarioClass.OUTPUT_FILENAME)
            return
    except NameError:
        pass

    scenario = ScenarioClass(duration=frames_count)

    window = ti.ui.Window("Quicksand Simulation", (1024, 1024), vsync=True)
    canvas = window.get_canvas()
    canvas.set_background_color((1, 1, 1))
    scene = ti.ui.Scene()
    camera = ti.ui.Camera()

    camera.position(0.5, 0.5, 2.0)
    camera.lookat(0.5, 0.5, 0.5)
    camera.up(0, 1, 0)
    scene.set_camera(camera)

    video_manager = ti.tools.VideoManager(
        output_dir="./result",
        framerate=30,
        automatic_build=False
    )

    frame = 0
    while window.running and frame < frames_count:
        scenario.step()
        
        camera.track_user_inputs(window, movement_speed=0.01, hold_key=ti.ui.RMB)
        scene.set_camera(camera)

        scene.ambient_light((0.5, 0.5, 0.5))
        scene.point_light(pos=(0.5, 1.5, 1.5), color=(1, 1, 1))

        if hasattr(scenario, 'particles'):
            scene.particles(
                scenario.particles, 
                per_vertex_color=scenario.particle_colors,
                radius=scenario.particle_radius
            )
        elif hasattr(scenario, 'render'):
            scenario.render(scene)

        canvas.scene(scene)
        img = window.get_image_buffer_as_numpy()
        video_manager.write_frame(img)

        window.show()
        print(f'Frame {frame}/{frames_count} | Particles: {scenario.pn_current}')
        frame += 1

    # 5. 导出视频
    print("Exporting video...")
    video_manager.make_video(gif=True, mp4=True)
    print("Done.")


def main():
    parser = argparse.ArgumentParser(description="Taichi Fluid Simulation")

    parser.add_argument(
        '--scenario',
        type=str,
        default='starry_water',
        choices=list(SCENARIO_MAP.keys()),
        help='Select which scenario to simulate.'
    )

    parser.add_argument(
        '--mode',
        type=str,
        default='gui',
        choices=['gui', 'render'],
        help='gui: run real-time window; render: export frames to GIF.'
    )

    parser.add_argument(
        '--frames',
        type=int,
        default=300,
        help='Number of frames (only used when mode=render).'
    )

    args = parser.parse_args()

    # Validate scenario
    if args.scenario not in SCENARIO_MAP:
        print(f"Error: Scenario '{args.scenario}' not found.")
        sys.exit(1)

    ScenarioClass = SCENARIO_MAP[args.scenario]

    # Run mode
    if args.mode == 'gui':
        run_gui(ScenarioClass)
    else:
        run_render(ScenarioClass, args.frames)


if __name__ == "__main__":
    main()
