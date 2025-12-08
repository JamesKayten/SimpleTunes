import SwiftUI

struct NowPlayingBar: View {
    @EnvironmentObject var player: PlayerViewModel
    @Binding var showQueue: Bool
    
    var body: some View {
        if let track = player.currentTrack {
            VStack(spacing: 0) {
                ProgressBar(value: player.currentTime, total: player.duration) { player.seek(to: $0) }
                
                HStack(spacing: 16) {
                    // Album art
                    RoundedRectangle(cornerRadius: 8).fill(.secondary.opacity(0.2)).frame(width: 56, height: 56)
                        .overlay { Image(systemName: player.isPlaying ? "waveform" : "music.note").font(.title2).foregroundStyle(.secondary) }
                    
                    // Track info
                    VStack(alignment: .leading, spacing: 4) {
                        Text(track.title).font(.headline).lineLimit(1)
                        Text(track.artist).font(.subheadline).foregroundStyle(.secondary).lineLimit(1)
                    }.frame(maxWidth: 200, alignment: .leading)
                    
                    // Favorite
                    Button { player.setFavorite(track, favorite: !(track.favorite ?? false)) } label: {
                        Image(systemName: track.favorite == true ? "heart.fill" : "heart")
                            .foregroundStyle(track.favorite == true ? .red : .secondary)
                    }.buttonStyle(.plain)
                    
                    // Rating
                    StarRatingView(rating: track.rating ?? 0) { player.setRating(track, rating: $0) }
                    
                    Spacer()
                    
                    // Shuffle
                    ControlButton(icon: "shuffle", isActive: player.shuffleEnabled) { player.toggleShuffle() }
                    
                    // Transport
                    HStack(spacing: 20) {
                        Button { player.skipBackward() } label: { Image(systemName: "backward.fill").font(.title2) }
                        Button { player.togglePlayPause() } label: {
                            Image(systemName: player.isPlaying ? "pause.circle.fill" : "play.circle.fill").font(.system(size: 44))
                        }
                        Button { player.skipForward() } label: { Image(systemName: "forward.fill").font(.title2) }
                    }.buttonStyle(.plain)
                    
                    // Repeat
                    ControlButton(icon: player.repeatMode == .one ? "repeat.1" : "repeat", isActive: player.repeatMode != .off) {
                        player.cycleRepeatMode()
                    }
                    
                    Spacer()
                    
                    // Time
                    TimeDisplay(current: player.currentTime, total: player.duration)
                    
                    // Volume
                    VolumeControl(volume: $player.volume) { player.setVolume($0) }
                    
                    // Queue toggle
                    ControlButton(icon: "list.bullet", isActive: showQueue) { withAnimation { showQueue.toggle() } }
                }
                .padding()
            }
            .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
        }
    }
}

struct ProgressBar: View {
    let value: Double, total: Double
    let onSeek: (Double) -> Void
    
    var progress: Double { total > 0 ? value / total : 0 }
    
    var body: some View {
        GeometryReader { geo in
            ZStack(alignment: .leading) {
                Rectangle().fill(.secondary.opacity(0.2))
                Rectangle().fill(.accent).frame(width: geo.size.width * progress)
            }
            .gesture(DragGesture(minimumDistance: 0).onChanged { v in
                onSeek(total * max(0, min(1, v.location.x / geo.size.width)))
            })
        }.frame(height: 4).clipShape(Capsule()).padding(.horizontal).padding(.top, 8)
    }
}

struct StarRatingView: View {
    let rating: Int
    let onRate: (Int) -> Void
    @State private var hover: Int? = nil
    
    var body: some View {
        HStack(spacing: 2) {
            ForEach(1...5, id: \.self) { star in
                Image(systemName: star <= (hover ?? rating) ? "star.fill" : "star")
                    .font(.system(size: 12))
                    .foregroundStyle(star <= (hover ?? rating) ? .yellow : .secondary.opacity(0.3))
                    .onTapGesture { onRate(star == rating ? 0 : star) }
                    .onHover { hover = $0 ? star : nil }
            }
        }
    }
}

struct ControlButton: View {
    let icon: String, isActive: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            Image(systemName: icon).font(.title3).foregroundStyle(isActive ? .accent : .primary)
        }.buttonStyle(.plain)
    }
}

struct TimeDisplay: View {
    let current: Double, total: Double
    
    var body: some View {
        HStack(spacing: 4) {
            Text(format(current)); Text("/").foregroundStyle(.secondary); Text(format(total))
        }.font(.caption).monospacedDigit().foregroundStyle(.secondary).frame(width: 80, alignment: .trailing)
    }
    
    private func format(_ s: Double) -> String { String(format: "%d:%02d", Int(s) / 60, Int(s) % 60) }
}

struct VolumeControl: View {
    @Binding var volume: Float
    let onChange: (Float) -> Void
    
    var icon: String {
        if volume == 0 { return "speaker.slash.fill" }
        if volume < 0.33 { return "speaker.wave.1.fill" }
        if volume < 0.66 { return "speaker.wave.2.fill" }
        return "speaker.wave.3.fill"
    }
    
    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: icon).font(.caption).foregroundStyle(.secondary)
            Slider(value: $volume, in: 0...1) { _ in onChange(volume) }.frame(width: 80)
        }
    }
}
