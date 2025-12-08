import SwiftUI

struct AlbumsView: View {
    @EnvironmentObject var player: PlayerViewModel
    @State private var viewMode: ViewMode = .grid
    
    enum ViewMode { case grid, list }
    let columns = [GridItem(.adaptive(minimum: 150, maximum: 180), spacing: 16)]
    
    var body: some View {
        Group {
            if viewMode == .grid {
                ScrollView {
                    LazyVGrid(columns: columns, spacing: 16) {
                        ForEach(player.albums) { album in
                            NavigationLink(destination: AlbumDetailView(album: album)) {
                                AlbumGridItem(album: album)
                            }.buttonStyle(.plain)
                        }
                    }.padding()
                }
            } else {
                List(player.albums) { album in
                    NavigationLink(destination: AlbumDetailView(album: album)) {
                        AlbumListRow(album: album)
                    }
                }
            }
        }
        .navigationTitle("Albums")
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Picker("View", selection: $viewMode) {
                    Image(systemName: "square.grid.2x2").tag(ViewMode.grid)
                    Image(systemName: "list.bullet").tag(ViewMode.list)
                }.pickerStyle(.segmented)
            }
        }
    }
}

struct AlbumGridItem: View {
    let album: Album
    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            RoundedRectangle(cornerRadius: 8).fill(.secondary.opacity(0.15)).aspectRatio(1, contentMode: .fit)
                .overlay { Image(systemName: "music.note").font(.system(size: 40)).foregroundStyle(.secondary) }
            Text(album.title).font(.subheadline).fontWeight(.medium).lineLimit(1)
            Text(album.artistName ?? "Unknown").font(.caption).foregroundStyle(.secondary).lineLimit(1)
        }
    }
}

struct AlbumListRow: View {
    let album: Album
    var body: some View {
        HStack {
            RoundedRectangle(cornerRadius: 4).fill(.secondary.opacity(0.2)).frame(width: 50, height: 50)
                .overlay { Image(systemName: "music.note").foregroundStyle(.secondary) }
            VStack(alignment: .leading) {
                Text(album.title).fontWeight(.medium)
                if let artist = album.artistName { Text(artist).font(.caption).foregroundStyle(.secondary) }
            }
            Spacer()
            if let year = album.year { Text(String(year)).font(.caption).foregroundStyle(.secondary) }
        }
    }
}

struct AlbumDetailView: View {
    let album: Album
    @EnvironmentObject var player: PlayerViewModel
    
    var tracks: [Track] {
        player.tracks.filter { $0.albumId == album.id }
            .sorted { ($0.discNumber ?? 1, $0.trackNumber ?? 0) < ($1.discNumber ?? 1, $1.trackNumber ?? 0) }
    }
    
    var body: some View {
        List {
            VStack(spacing: 12) {
                RoundedRectangle(cornerRadius: 8).fill(.secondary.opacity(0.15)).frame(width: 200, height: 200)
                    .overlay { Image(systemName: "music.note").font(.system(size: 50)).foregroundStyle(.secondary) }
                Text(album.title).font(.title2).fontWeight(.bold)
                if let artist = album.artistName { Text(artist).foregroundStyle(.secondary) }
                Button("Play All") { player.playQueue(tracks: tracks) }.buttonStyle(.borderedProminent)
            }.frame(maxWidth: .infinity).padding(.vertical)
            
            ForEach(Array(tracks.enumerated()), id: \.element.id) { i, track in
                TrackRow(track: track).contentShape(Rectangle())
                    .onTapGesture { player.playQueue(tracks: tracks, startIndex: i) }
                    .contextMenu { TrackContextMenu(track: track) }
            }
        }.listStyle(.plain).navigationTitle(album.title)
    }
}
