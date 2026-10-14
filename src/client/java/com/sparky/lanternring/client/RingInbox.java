package com.sparky.lanternring.client;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.mojang.blaze3d.platform.NativeImage;
import com.sparky.lanternring.Corps;
import com.sparky.lanternring.LanternRing;
import com.sparky.lanternring.item.PowerRingItem;
import java.io.IOException;
import java.io.InputStream;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Base64;
import java.util.Comparator;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.stream.Stream;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.client.Minecraft;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.ItemStack;

/**
 * Ring Lab's "Send to Claude": files a GitHub issue labelled claude-inbox on the mod's repo, using the
 * updater's token (it needs Issues: Read and write as well). The issue carries the jar version, the held
 * ring's corps and mode, the Ring Lab report and, if asked, the newest F2 screenshot. GitHub issues can't
 * hold uploaded images through the API, so the screenshot goes in as base64 PNG text in follow-up
 * comments, which the inbox routine decodes.
 */
public final class RingInbox {
	public static final String LABEL = "claude-inbox";
	private static final String ISSUES = "https://api.github.com/repos/sparkygogo77-spec/site-10/issues";
	/** GitHub's comment limit is 65536 characters; stay well under it. */
	private static final int CHUNK = 60000;
	private static final int MAX_CHUNKS = 3;

	public enum Action {
		REDO("Redo / Retry"), APPROVE("Approve"), REMOVE("Remove"), NOTE("Note");

		public final String label;

		Action(String label) {
			this.label = label;
		}
	}

	private static HttpClient http;

	private RingInbox() {
	}

	/** The newest screenshot in the game's screenshots folder, or null. */
	public static Path latestScreenshot() {
		Path dir = FabricLoader.getInstance().getGameDir().resolve("screenshots");
		if (!Files.isDirectory(dir)) return null;
		try (Stream<Path> files = Files.list(dir)) {
			return files.filter(p -> p.getFileName().toString().endsWith(".png"))
					.max(Comparator.comparingLong(p -> p.toFile().lastModified())).orElse(null);
		} catch (IOException e) {
			return null;
		}
	}

	/**
	 * Builds the issue on the game thread (it reads the player and settings), then sends it off-thread.
	 * The future completes with the issue's URL, or fails with a short reason fit to show in game.
	 */
	public static CompletableFuture<String> send(Action action, String text, boolean withScreenshot) {
		String token = RingUpdater.token();
		if (token.isBlank()) return CompletableFuture.failedFuture(new IOException("Paste a GitHub token in Updates first."));
		String note = text == null ? "" : text.strip();
		String title = "[Ring Lab] " + action.label + (note.isEmpty() ? "" : ": " + shorten(note, 70));
		StringBuilder body = new StringBuilder();
		body.append("**Action:** ").append(action.label).append('\n');
		body.append("**Version:** ").append(LanternRing.version()).append('\n');
		body.append("**Ring:** ").append(ringLine()).append("\n\n");
		body.append(note.isEmpty() ? "_(no note typed here)_" : note).append("\n\n");
		String rowNotes = rowNotes();
		if (!rowNotes.isEmpty()) body.append("**Notes on rows:**\n").append(rowNotes).append('\n');
		body.append("<details><summary>Ring Lab report</summary>\n\n```\n").append(LabSettings.get().report()).append("```\n</details>\n");
		Path shot = withScreenshot ? latestScreenshot() : null;
		if (withScreenshot && shot == null) return CompletableFuture.failedFuture(new IOException("No screenshot yet. Press F2 in game first."));
		if (shot != null) body.append("\nScreenshot: ").append(shot.getFileName()).append(" (base64 PNG in the comments below)\n");
		body.append("\n_Sent from the Ring Lab._\n");

		JsonObject issue = new JsonObject();
		issue.addProperty("title", title);
		issue.addProperty("body", body.toString());
		JsonArray labels = new JsonArray();
		labels.add(LABEL);
		issue.add("labels", labels);

		return CompletableFuture.supplyAsync(() -> {
			try {
				List<String> chunks = shot == null ? List.of() : screenshotChunks(shot);
				JsonObject created = post(token, ISSUES, issue);
				String url = created.get("html_url").getAsString();
				int number = created.get("number").getAsInt();
				for (int i = 0; i < chunks.size(); i++) {
					JsonObject comment = new JsonObject();
					comment.addProperty("body", "screenshot part " + (i + 1) + "/" + chunks.size() + "\n```base64\n" + chunks.get(i) + "\n```");
					post(token, ISSUES + "/" + number + "/comments", comment);
				}
				return url;
			} catch (IOException e) {
				throw new RuntimeException(e.getMessage(), e);
			} catch (InterruptedException e) {
				Thread.currentThread().interrupt();
				throw new RuntimeException("Interrupted.", e);
			}
		});
	}

	/** Every ✎ note left on a Ring Lab row, one "- row, take: note" line each. */
	private static String rowNotes() {
		LabSettings s = LabSettings.get();
		StringBuilder out = new StringBuilder();
		for (LabSettings.Option<?> option : LabSettings.OPTIONS) {
			for (Enum<?> value : option.type().getEnumConstants()) {
				String note = s.note(option.key() + "." + value.name());
				if (note.isEmpty()) continue;
				out.append("- ").append(option.label()).append(", ").append(value.name()).append(": ").append(note.replaceAll("\\s*\\R\\s*", " / ")).append('\n');
			}
		}
		return out.toString();
	}

	/** "Green, mode Blast" for the ring in hand, or a note that none is held. */
	private static String ringLine() {
		Player player = Minecraft.getInstance().player;
		if (player == null) return "not in a world";
		ItemStack ring = com.sparky.lanternring.RingSlot.ring(player);
		if (!(ring.getItem() instanceof PowerRingItem)) return "none in hand";
		Corps corps = Corps.of(ring);
		return corps.getSerializedName() + ", mode " + corps.modeName(PowerRingItem.getMode(ring)).getString();
	}

	/** The screenshot, shrunk until its base64 fits in a few comments, split into comment-sized pieces. */
	public static List<String> screenshotChunks(Path file) throws IOException {
		try (InputStream in = Files.newInputStream(file); NativeImage full = NativeImage.read(in)) {
			for (int width = 640; width >= 160; width = width * 3 / 4) {
				byte[] png = scaled(full, width);
				String b64 = Base64.getEncoder().encodeToString(png);
				if (b64.length() <= CHUNK * MAX_CHUNKS) {
					List<String> out = new ArrayList<>();
					for (int i = 0; i < b64.length(); i += CHUNK) out.add(b64.substring(i, Math.min(b64.length(), i + CHUNK)));
					return out;
				}
			}
		}
		throw new IOException("Screenshot too big to send.");
	}

	/** A box-filtered copy at most `width` pixels wide, as PNG bytes. */
	private static byte[] scaled(NativeImage src, int width) throws IOException {
		int w = Math.min(width, src.getWidth());
		int h = Math.max(1, Math.round(src.getHeight() * (w / (float) src.getWidth())));
		try (NativeImage out = new NativeImage(w, h, false)) {
			for (int y = 0; y < h; y++) {
				int y0 = y * src.getHeight() / h, y1 = Math.max(y0 + 1, (y + 1) * src.getHeight() / h);
				for (int x = 0; x < w; x++) {
					int x0 = x * src.getWidth() / w, x1 = Math.max(x0 + 1, (x + 1) * src.getWidth() / w);
					long a = 0, r = 0, g = 0, b = 0;
					int n = 0;
					for (int sy = y0; sy < y1; sy++) {
						for (int sx = x0; sx < x1; sx++) {
							int c = src.getPixel(sx, sy);
							a += c >>> 24;
							r += (c >> 16) & 0xFF;
							g += (c >> 8) & 0xFF;
							b += c & 0xFF;
							n++;
						}
					}
					out.setPixel(x, y, (int) (a / n) << 24 | (int) (r / n) << 16 | (int) (g / n) << 8 | (int) (b / n));
				}
			}
			Path tmp = Files.createTempFile("lantern-inbox", ".png");
			try {
				out.writeToFile(tmp);
				return Files.readAllBytes(tmp);
			} finally {
				Files.deleteIfExists(tmp);
			}
		}
	}

	private static JsonObject post(String token, String url, JsonObject json) throws IOException, InterruptedException {
		HttpRequest request = HttpRequest.newBuilder(URI.create(url))
				.header("Accept", "application/vnd.github+json")
				.header("Authorization", "Bearer " + token)
				.header("X-GitHub-Api-Version", "2022-11-28")
				.header("User-Agent", "lantern-ring-inbox")
				.timeout(Duration.ofSeconds(30))
				.POST(HttpRequest.BodyPublishers.ofString(json.toString(), StandardCharsets.UTF_8))
				.build();
		HttpResponse<String> response;
		try {
			response = client().send(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
		} catch (IOException e) {
			throw new IOException("Couldn't reach GitHub.");
		}
		int code = response.statusCode();
		if (code == 401) throw new IOException("GitHub refused the token (401).");
		if (code == 403 || code == 404) throw new IOException("Token can't file issues (" + code + "). Give it Issues: Read and write.");
		if (code / 100 != 2) throw new IOException("GitHub said " + code + ".");
		return JsonParser.parseString(response.body()).getAsJsonObject();
	}

	private static String shorten(String text, int max) {
		String line = text.replaceAll("\\s+", " ");
		return line.length() <= max ? line : line.substring(0, max - 3) + "...";
	}

	private static HttpClient client() {
		if (http == null) http = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build();
		return http;
	}
}
