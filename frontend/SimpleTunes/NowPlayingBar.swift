import SwiftUI

struct NowPlayingBar: View {
    @EnvironmentObject var player: PlayerViewModel
    
    var body: some View {
        if let track = player.currentTrack {
            VStack(spacing: 8) {
                ProgressView(value: player.currentTime, total: max(player.duration, 1))
                    .progressViewStyle(.linear)
                
                HStack(spacing: 20) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(track.title).font(.headline).lineLimit(1)
                        Text(track.artist).font(.subheadline).foregroundStyle(.secondary).lineLimit(1)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                    
                    HStack(spacing: 24) {
                        Button(action: { player.skipBackward() }) {
                            Image(systemName: "backward.fill").font(.title2)
                        }
                        Button(action: { player.togglePlayPause() }) {
                            Image(systemName: player.isPlaying ? "pause.fill" : "play.fill").font(.title)
                        }
                        Button(action: { player.skipForward() }) {
                            Image(systemName: "forward.fill").font(.title2)
                        }
                    }
                    .buttonStyle(.plain)
                    
                    HStack(spacing: 4) {
                        Text(formatTime(player.currentTime))
                        Text("/").foregroundStyle(.secondary)
                        Text(formatTime(player.duration))
                    }
                    .font(.caption)
                    .monospacedDigit()
                    .foregroundStyle(.secondary)
                }
            }
            .padding()
            .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
        }
    }
    
    private func formatTime(_ s: Double) -> String {
        String(format: "%d:%02d", Int(s) / 60, Int(s) % 60)
    }
}
