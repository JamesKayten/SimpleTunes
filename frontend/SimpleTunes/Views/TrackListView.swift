import SwiftUI

struct TrackListView: View {
    @EnvironmentObject var player: PlayerViewModel
    
    var body: some View {
        List(player.filteredTracks) { track in
            TrackRow(track: track)
                .contentShape(Rectangle())
                .onTapGesture { player.play(track: track) }
                .contextMenu { TrackContextMenu(track: track) }
        }
        .listStyle(.plain)
        .navigationTitle("All Tracks")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Menu {
                    Button("Play All") { player.playQueue(tracks: player.filteredTracks) }
                    Button("Shuffle All") {
                        player.shuffleEnabled = true
                        player.playQueue(tracks: player.filteredTracks.shuffled())
                    }
                } label: { Image(systemName: "ellipsis.circle") }
            }
        }
    }
}

struct TrackRow: View {
    let track: Track
    @EnvironmentObject var player: PlayerViewModel
    
    var isCurrentTrack: Bool { player.currentTrack?.id == track.id }
    
    var body: some View {
        HStack(spacing: 12) {
            ZStack {
                if isCurrentTrack && player.isPlaying {
                    Image(systemName: "speaker.wave.2.fill").foregroundStyle(.accent).font(.caption)
                } else if let num = track.trackNumber {
                    Text("\(num)").font(.caption).foregroundStyle(.secondary)
                } else {
                    Image(systemName: "music.note").font(.caption).foregroundStyle(.secondary)
                }
            }.frame(width: 24)
            
            VStack(alignment: .leading, spacing: 2) {
                HStack {
                    Text(track.title)
                        .fontWeight(isCurrentTrack ? .semibold : .regular)
                        .foregroundStyle(isCurrentTrack ? .accent : .primary)
                        .lineLimit(1)
                    if track.favorite == true {
                        Image(systemName: "heart.fill").font(.caption2).foregroundStyle(.red)
                    }
                }
                Text("\(track.artist) • \(track.album)")
                    .font(.caption).foregroundStyle(.secondary).lineLimit(1)
            }
            
            Spacer()
            
            if let rating = track.rating, rating > 0 {
                HStack(spacing: 1) {
                    ForEach(1...rating, id: \.self) { _ in
                        Image(systemName: "star.fill").font(.system(size: 8)).foregroundStyle(.yellow)
                    }
                }
            }
            
            Text(track.durationFormatted).font(.caption).foregroundStyle(.secondary).monospacedDigit()
        }
        .padding(.vertical, 4)
    }
}

struct TrackContextMenu: View {
    let track: Track
    @EnvironmentObject var player: PlayerViewModel
    
    var body: some View {
        Button { player.play(track: track) } label: { Label("Play", systemImage: "play") }
        Button { player.playNext(track) } label: { Label("Play Next", systemImage: "text.insert") }
        Button { player.addToQueue(track) } label: { Label("Add to Queue", systemImage: "text.append") }
        
        Divider()
        
        Button {
            player.setFavorite(track, favorite: !(track.favorite ?? false))
        } label: {
            Label(track.favorite == true ? "Remove from Favorites" : "Add to Favorites",
                  systemImage: track.favorite == true ? "heart.slash" : "heart")
        }
        
        Menu {
            ForEach(1...5, id: \.self) { stars in
                Button { player.setRating(track, rating: stars) } label: {
                    Label(String(repeating: "★", count: stars), systemImage: "\(stars).circle")
                }
            }
            Divider()
            Button { player.setRating(track, rating: 0) } label: { Label("Clear Rating", systemImage: "xmark.circle") }
        } label: { Label("Rate", systemImage: "star") }
        
        Divider()
        
        Menu {
            ForEach(player.playlists) { playlist in
                Button { player.addToPlaylist(track, playlistId: playlist.id) } label: { Text(playlist.name) }
            }
        } label: { Label("Add to Playlist", systemImage: "text.badge.plus") }
        
        Divider()
        
        Button { NSWorkspace.shared.selectFile(track.path, inFileViewerRootedAtPath: "") } label: {
            Label("Show in Finder", systemImage: "folder")
        }
    }
}
