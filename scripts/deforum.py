import scripts.deforum.args as deforum_args

import modules.scripts as wscripts
from modules import script_callbacks
import gradio as gr

from modules.processing import Processed, StableDiffusionProcessingImg2Img, process_images
from PIL import Image
import gc
import torch
import os, sys
from modules.shared import opts, cmd_opts, state
from modules.ui import setup_progressbar
from types import SimpleNamespace

class DeforumScript(wscripts.Script):

    def title(self):
        return "Deforum v0.5-webui-beta"

    def ui(self, is_img2img):
        return deforum_args.setup_deforum_setting_ui(self, is_img2img, is_extension = False)
        
    def show(self, is_img2img):
        return is_img2img
    
    def run(self, p, override_settings_with_file, custom_settings_file, animation_mode, max_frames, border, angle, zoom, translation_x, translation_y, translation_z, rotation_3d_x, rotation_3d_y, rotation_3d_z, flip_2d_perspective, perspective_flip_theta, perspective_flip_phi, perspective_flip_gamma, perspective_flip_fv, noise_schedule, strength_schedule, contrast_schedule, cfg_scale_schedule, seed_schedule, color_coherence, diffusion_cadence, use_depth_warping, midas_weight, near_plane, far_plane, fov, padding_mode, sampling_mode, save_depth_maps, video_init_path, extract_nth_frame, overwrite_extracted_frames, use_mask_video, video_mask_path, interpolate_key_frames, interpolate_x_frames, resume_from_timestring, resume_timestring, prompts, animation_prompts, W, H, restore_faces, tiling, enable_hr, firstphase_width, firstphase_height, seed, sampler, seed_enable_extras, subseed_strength, seed_resize_from_w, seed_resize_from_h, steps, ddim_eta, n_batch, make_grid, grid_rows, save_settings, save_samples, display_samples, save_sample_per_step, show_sample_per_step, override_these_with_webui, batch_name, filename_format, seed_behavior, use_init, from_img2img_instead_of_link, strength_0_no_init, strength, init_image, use_mask, use_alpha_as_mask, invert_mask, overlay_mask, mask_file, mask_brightness_adjust, mask_overlay_blur, skip_video_for_run_all, fps, output_format, ffmpeg_location, add_soundtrack, soundtrack_path, use_manual_settings, render_steps, max_video_frames, path_name_modifier, image_path, mp4_path, i1, i2, i3, i4, i5, i6, i7, i8, i9, i10, i11, i12, i13, i14, i15, i16, i17, i18, i19, i20, i21, i22, i23, i24, i25, i26, i27, i28, i29, i30, i31, i32, i33, i34, i35, i36):
        print('Deforum script for 2D, pseudo-2D and 3D animations')
        print('v0.5-webui-beta')
        
        root, args, anim_args, video_args = deforum_args.process_args(self, p, override_settings_with_file, custom_settings_file, animation_mode, max_frames, border, angle, zoom, translation_x, translation_y, translation_z, rotation_3d_x, rotation_3d_y, rotation_3d_z, flip_2d_perspective, perspective_flip_theta, perspective_flip_phi, perspective_flip_gamma, perspective_flip_fv, noise_schedule, strength_schedule, contrast_schedule, cfg_scale_schedule, seed_schedule, color_coherence, diffusion_cadence, use_depth_warping, midas_weight, near_plane, far_plane, fov, padding_mode, sampling_mode, save_depth_maps, video_init_path, extract_nth_frame, overwrite_extracted_frames, use_mask_video, video_mask_path, interpolate_key_frames, interpolate_x_frames, resume_from_timestring, resume_timestring, prompts, animation_prompts, W, H, seed, sampler, steps, ddim_eta, n_batch, make_grid, grid_rows, save_settings, save_samples, display_samples, save_sample_per_step, show_sample_per_step, override_these_with_webui, batch_name, filename_format, seed_behavior, use_init, from_img2img_instead_of_link, strength_0_no_init, strength, init_image, use_mask, use_alpha_as_mask, invert_mask, overlay_mask, mask_file, mask_brightness_adjust, mask_overlay_blur, skip_video_for_run_all, fps, output_format, ffmpeg_location, add_soundtrack, soundtrack_path, use_manual_settings, render_steps, max_video_frames, path_name_modifier, image_path, mp4_path, i1, i2, i3, i4, i5, i6, i7, i8, i9, i10, i11, i12, i13, i14, i15, i16, i17, i18, i19, i20, i21, i22, i23, i24, i25, i26, i27, i28, i29, i30, i31, i32, i33, i34, i35, i36)
        
        # Install numexpr as it's the thing most people are having problems with
        from launch import is_installed, run_pip
        if not is_installed("numexpr"):
            run_pip("install numexpr", "numexpr")
        
        sys.path.extend([
            os.getcwd()+'/scripts/deforum/src',
            os.getcwd()+'/extensions/deforum/scripts/deforum/src'
        ])
        
        # clean up unused memory
        gc.collect()
        torch.cuda.empty_cache()
        
        from scripts.deforum.render import render_animation, render_input_video

        # dispatch to appropriate renderer
        if anim_args.animation_mode == '2D' or anim_args.animation_mode == '3D':
            render_animation(args, anim_args, root.animation_prompts, root)
        elif anim_args.animation_mode == 'Video Input':
            render_input_video(args, anim_args, root.animation_prompts, root)#TODO: prettify code
        else:
            print('Other modes are not available yet!')
        
        from base64 import b64encode
        
        if video_args.skip_video_for_run_all:
            print('Skipping video creation, uncheck skip_video_for_run_all if you want to run it')
        elif video_args.output_format == 'FFMPEG mp4':
            import subprocess

            if video_args.use_manual_settings:
                max_video_frames = video_args.max_video_frames #@param {type:"string"}
                image_path = video_args.image_path
                mp4_path = video_args.mp4_path
            else:
                path_name_modifier = video_args.path_name_modifier
                if video_args.render_steps: # render steps from a single image
                    fname = f"{path_name_modifier}_%05d.png"
                    all_step_dirs = [os.path.join(args.outdir, d) for d in os.listdir(args.outdir) if os.path.isdir(os.path.join(args.outdir,d))]
                    newest_dir = max(all_step_dirs, key=os.path.getmtime)
                    image_path = os.path.join(newest_dir, fname)
                    print(f"Reading images from {image_path}")
                    mp4_path = os.path.join(newest_dir, f"{args.timestring}_{path_name_modifier}.mp4")
                    max_video_frames = args.steps
                else: # render images for a video
                    image_path = os.path.join(args.outdir, f"{args.timestring}_%05d.png")
                    mp4_path = os.path.join(args.outdir, f"{args.timestring}.mp4")
                    max_video_frames = anim_args.max_frames

            print(f"{image_path} -> {mp4_path}")
            
            # make video
            cmd = [
                video_args.ffmpeg_location,
                '-y',
                '-vcodec', 'png',
                '-r', str(int(fps)),
                '-start_number', str(0),
                '-i', image_path,
                '-frames:v', str(max_video_frames),
                '-c:v', 'libx264',
                '-vf',
                f'fps={int(fps)}',
                '-pix_fmt', 'yuv420p',
                '-crf', '17',
                '-preset', 'veryfast',
                '-pattern_type', 'sequence',
                mp4_path
            ]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if process.returncode != 0:
                print(stderr)
                raise RuntimeError(stderr)
                
            if video_args.add_soundtrack:
                cmd = [
                    video_args.ffmpeg_location,
                    '-i',
                    mp4_path,
                    '-i',
                    video_args.soundtrack_path,
                    '-map', '0:v',
                    '-map', '1:a',
                    '-c:v', 'copy',
                    '-shortest',
                    mp4_path+'.temp.mp4'
                ]
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = process.communicate()
                if process.returncode != 0:
                    print(stderr)
                    raise RuntimeError(stderr)
                os.replace(mp4_path+'.temp.mp4', mp4_path)

            mp4 = open(mp4_path,'rb').read()
            data_url = "data:video/mp4;base64," + b64encode(mp4).decode()
            
            deforum_args.i1_store = f'<p style=\"font-weight:bold;margin-bottom:0.75em\">Deforum v0.5-webui-beta</p><video controls loop><source src="{data_url}" type="video/mp4"></video>'
        else:
            if video_args.use_manual_settings:
                max_video_frames = video_args.max_video_frames #@param {type:"string"}
                image_path = video_args.image_path
                mp4_path = video_args.mp4_path
            else:
                path_name_modifier = video_args.path_name_modifier
                if video_args.render_steps: # render steps from a single image
                    fname = f"{path_name_modifier}_%05d.png"
                    all_step_dirs = [os.path.join(args.outdir, d) for d in os.listdir(args.outdir) if os.path.isdir(os.path.join(args.outdir,d))]
                    newest_dir = max(all_step_dirs, key=os.path.getmtime)
                    image_path = os.path.join(newest_dir, fname)
                    print(f"Reading images from {image_path}")
                    mp4_path = os.path.join(newest_dir, f"{args.timestring}_{path_name_modifier}.gif")
                    max_video_frames = args.steps
                else: # render images for a video
                    image_path = os.path.join(args.outdir, f"{args.timestring}_%05d.png")
                    mp4_path = os.path.join(args.outdir, f"{args.timestring}.gif")
                    max_video_frames = anim_args.max_frames

            print(f"{image_path} -> {mp4_path}")
            
            imagelist = [Image.open(os.path.join(args.outdir, image_path%d)) for d in range(max_video_frames) if os.path.exists(os.path.join(args.outdir, image_path%d))]
            
            imagelist[0].save(
                mp4_path,#gif here
                save_all=True,
                append_images=imagelist[1:],
                optimize=True,
                duration=1000/fps,
                loop=0
            )
            
            mp4 = open(mp4_path,'rb').read()
            data_url = "data:image/gif;base64," + b64encode(mp4).decode()
            
            deforum_args.i1_store = f'<p style=\"font-weight:bold;margin-bottom:0.75em\">Deforum v0.5-webui-beta</p><img src="{data_url}" type="image/gif"></img>'
    
        if root.initial_info is None:
            root.initial_info = "An error has occured and nothing has been generated!"
            root.initial_info += "\nPlease, report the bug to https://github.com/deforum-art/deforum-for-automatic1111-webui/issues"
            import numpy as np
            a = np.random.rand(args.W, args.H, 3)*255
            root.first_frame = Image.fromarray(a.astype('uint8')).convert('RGB')
            root.initial_seed = 6934
        root.initial_info += "\n The animation is stored in " + args.outdir + '\n'
        root.initial_info += "Only the first frame is shown in webui not to clutter the memory"
        return Processed(p, [root.first_frame], root.initial_seed, root.initial_info)

def run_deforum(**args):
    p = StableDiffusionProcessingImg2Img(
        sd_model=shared.sd_model
        #we'll setup the rest later
    )

    args.override_these_with_webui = False

    processed = DeforumScript.run(p, args)
    if processed is None:
        processed = process_images(p)

    shared.total_tqdm.clear()

    generation_info_js = processed.js()
    if opts.samples_log_stdout:
        print(generation_info_js)

    if opts.do_not_show_images:
        processed.images = []
    return processed.images, generation_info_js, plaintext_to_html(processed.info)

def on_ui_tabs():
    with gr.Blocks(analytics_enabled=False) as deforum_interface:
        components = {}
        with gr.Row(elem_id='deforum_progress_row').style(equal_height=False):
            with gr.Column(scale=1, variant='panel'):
                components = deforum_args.setup_deforum_setting_dictionary(None, True, True)
        
            with gr.Column(scale=1):
                with gr.Row():
                    btn = gr.Button("Click here after the generation to show the video")
                    components['btn'] = btn
                with gr.Row():
                    i1 = gr.HTML(deforum_args.i1_store, elem_id='deforum_header')
                    components['i1'] = i1
                    def show_vid():
                        return {
                            i1: gr.update(value=deforum_args.i1_store, visible=True)
                        }
                
                    btn.click(
                        show_vid,
                        [],
                        [i1]
                        )
                with gr.Row(elem_id='toprow'):
                    id_part = 'deforum'
                    skip = gr.Button('Skip', elem_id=f"{id_part}_skip")
                    interrupt = gr.Button('Interrupt', elem_id=f"{id_part}_interrupt")
                    submit = gr.Button('Generate', elem_id=f"{id_part}_generate", variant='primary')

                    skip.click(
                        fn=lambda: state.skip(),
                        inputs=[],
                        outputs=[],
                    )

                    interrupt.click(
                        fn=lambda: state.interrupt(),
                        inputs=[],
                        outputs=[],
                    )

                    submit.click(
                        fn=lambda: print('deforum submitted'),
                        _js = "submit_deforum",
                        inputs=[],
                        outputs=[],
                    )
                progressbar = gr.HTML(elem_id="deforum_progressbar")
                deforum_preview = gr.Image(elem_id='deforum_preview', visible=False)
                setup_progressbar(progressbar, deforum_preview, 'deforum')
                deforum_gallery = gr.Gallery(label='Output', show_label=False, elem_id='deforum_gallery').style(grid=4)
                with gr.Group():
                    html_info = gr.HTML()
                    generation_info = gr.Textbox(visible=False)

    components['override_these_with_webui'].visible = False

    ds = SimpleNamespace(**components)
    component_list = [ds.btn, ds.override_settings_with_file, ds.custom_settings_file, ds.animation_mode, ds.max_frames, ds.border, ds.angle, ds.zoom, ds.translation_x, ds.translation_y, ds.translation_z, ds.rotation_3d_x, ds.rotation_3d_y, ds.rotation_3d_z, ds.flip_2d_perspective, ds.perspective_flip_theta, ds.perspective_flip_phi, ds.perspective_flip_gamma, ds.perspective_flip_fv, ds.noise_schedule, ds.strength_schedule, ds.contrast_schedule, ds.cfg_scale_schedule, ds.seed_schedule, ds.color_coherence, ds.diffusion_cadence, ds.use_depth_warping, ds.midas_weight, ds.near_plane, ds.far_plane, ds.fov, ds.padding_mode, ds.sampling_mode, ds.save_depth_maps, ds.video_init_path, ds.extract_nth_frame, ds.overwrite_extracted_frames, ds.use_mask_video, ds.video_mask_path, ds.interpolate_key_frames, ds.interpolate_x_frames, ds.resume_from_timestring, ds.resume_timestring, ds.prompts, ds.animation_prompts, ds.W, ds.H, ds.restore_faces, ds.tiling, ds.enable_hr, ds.firstphase_width, ds.firstphase_height, ds.seed, ds.sampler, ds.seed_enable_extras, ds.subseed_strength, ds.seed_resize_from_w, ds.seed_resize_from_h, ds.steps, ds.ddim_eta, ds.n_batch, ds.make_grid, ds.grid_rows, ds.save_settings, ds.save_samples, ds.display_samples, ds.save_sample_per_step, ds.show_sample_per_step, ds.override_these_with_webui, ds.batch_name, ds.filename_format, ds.seed_behavior, ds.use_init, ds.from_img2img_instead_of_link, ds.strength_0_no_init, ds.strength, ds.init_image, ds.use_mask, ds.use_alpha_as_mask, ds.invert_mask, ds.overlay_mask, ds.mask_file, ds.mask_brightness_adjust, ds.mask_overlay_blur, ds.skip_video_for_run_all, ds.fps, ds.output_format, ds.ffmpeg_location, ds.add_soundtrack, ds.soundtrack_path, ds.use_manual_settings, ds.render_steps, ds.max_video_frames, ds.path_name_modifier, ds.image_path, ds.mp4_path, ds.i1, ds.i2, ds.i3, ds.i4, ds.i5, ds.i6, ds.i7, ds.i8, ds.i9, ds.i10, ds.i11, ds.i12, ds.i13, ds.i14, ds.i15, ds.i16, ds.i17, ds.i18, ds.i19, ds.i20, ds.i21, ds.i22, ds.i23, ds.i24, ds.i25, ds.i26, ds.i27, ds.i28, ds.i29, ds.i30, ds.i31, ds.i32, ds.i33, ds.i34, ds.i35, ds.i36]

    deforum_args = dict(
                fn=wrap_gradio_gpu_call(run_deforum),
                _js="submit_deforum",
                inputs=component_list,

                outputs=[
                    deforum_gallery,
                    generation_info,
                    html_info
                ],
                show_progress=False,
            )

    submit.click(**deforum_args)

    return [(deforum_interface, "Deforum", "deforum_interface")]

script_callbacks.on_ui_tabs(on_ui_tabs)
