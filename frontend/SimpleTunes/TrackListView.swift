import SwiftUI

struct TrackListView: View {
    @EnvironmentObject var player: PlayerViewModel
    
    var body: some View {
        List(player.filteredTracks) { track in
            TrackRow(track: track)
                .contentShape(Rectangle())
                .onTapGesture { player.play(track: track) }
        }
        .listStyle(.plain)
        .navigationTitle("All Tracks")
    }
}

struct TrackRow: View {
    let track: Track
    @EnvironmentObject var player: PlayerViewModel
    
    var isPlaying: Bool { player.currentTrack?.id == track.id }
    
    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text(track.title)
                    .fontWeight(isPlaying ? .semibold : .regular)
                    .foregroundStyle(isPlaying ? .accent : .primary)
                Text("\(track.artist) • \(track.album)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Spacer()
            if isPlaying && player.isPlaying {
                Image(systemName: "speaker.wave.2.fill")
                    .foregroundStyle(.accent)
            }
            Text(track.durationFormatted)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding(.vertical, 4)
    }
}
