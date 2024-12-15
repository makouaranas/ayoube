from flask import Flask, render_template, request, send_file, jsonify
from pytube import YouTube, Playlist
import os
import re

app = Flask(__name__)

# Ensure downloads directory exists
if not os.path.exists('downloads'):
    os.makedirs('downloads')

def sanitize_filename(filename):
    # Remove invalid characters from filename
    return re.sub(r'[<>:"/\\|?*]', '', filename)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    if request.method != 'POST':
        return jsonify({'status': 'error', 'message': 'Method not allowed'}), 405
    
    try:
        url = request.form.get('url')
        format_type = request.form.get('format')
        
        if not url or not format_type:
            return jsonify({
                'status': 'error',
                'message': 'Missing URL or format parameter'
            }), 400

        if 'playlist' in url.lower():
            # Handle playlist download
            playlist = Playlist(url)
            downloaded_files = []
            
            for video in playlist.videos:
                try:
                    filename = sanitize_filename(video.title)
                    if format_type == 'mp3':
                        stream = video.streams.filter(only_audio=True).first()
                        file_path = stream.download(
                            output_path='downloads',
                            filename=f"{filename}.mp3"
                        )
                    else:  # mp4
                        stream = video.streams.get_highest_resolution()
                        file_path = stream.download(
                            output_path='downloads',
                            filename=f"{filename}.mp4"
                        )
                    downloaded_files.append(os.path.basename(file_path))
                except Exception as e:
                    print(f"Error downloading {video.title}: {str(e)}")
                    continue
            
            if not downloaded_files:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to download any files from the playlist'
                }), 400
                
            return jsonify({
                'status': 'success',
                'message': f'Successfully downloaded {len(downloaded_files)} files from playlist',
                'files': downloaded_files
            })
        
        else:
            # Handle single video download
            yt = YouTube(url)
            filename = sanitize_filename(yt.title)
            
            try:
                if format_type == 'mp3':
                    stream = yt.streams.filter(only_audio=True).first()
                    if not stream:
                        return jsonify({
                            'status': 'error',
                            'message': 'No audio stream available for this video'
                        }), 400
                    file_path = stream.download(
                        output_path='downloads',
                        filename=f"{filename}.mp3"
                    )
                else:  # mp4
                    stream = yt.streams.get_highest_resolution()
                    if not stream:
                        return jsonify({
                            'status': 'error',
                            'message': 'No video stream available'
                        }), 400
                    file_path = stream.download(
                        output_path='downloads',
                        filename=f"{filename}.mp4"
                    )
                
                return jsonify({
                    'status': 'success',
                    'message': 'Download completed successfully',
                    'file': os.path.basename(file_path)
                })
                
            except Exception as e:
                print(f"Error downloading video: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'message': f'Error downloading video: {str(e)}'
                }), 400
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

if __name__ == '__main__':
    app.run(debug=True)
