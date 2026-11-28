// Isolated native WinForms target for real foreground UIA qualification.
// Compiler output is placed under a unique test-only TEMP directory.
// Never opens or modifies another application or document.
using System;
using System.Drawing;
using System.IO;
using System.Text;
using System.Windows.Forms;

internal sealed class UniversalCourierFixture : Form
{
    private readonly string root;
    private readonly TextBox editor;
    private readonly Label posted;
    private readonly bool withSend;
    private int clicks;

    private UniversalCourierFixture(string title, string dir, string initial, bool button)
    {
        root = Path.GetFullPath(dir);
        Directory.CreateDirectory(root);
        withSend = button;
        Text = title;
        StartPosition = FormStartPosition.CenterScreen;
        Width = 770;
        Height = 200;
        TopMost = true;
        MaximizeBox = false;
        MinimizeBox = false;
        editor = new TextBox();
        editor.SetBounds(16,16,690,28);
        editor.AccessibleName = "Courier qualification input";
        editor.Text = initial;
        Controls.Add(editor);
        posted = new Label();
        posted.SetBounds(16,100,690,28);
        Controls.Add(posted);
        if (withSend)
        {
            var send = new Button();
            send.SetBounds(16,54,120,32);
            send.Text = "Send";
            send.AccessibleName = "Send";
            send.Click += delegate(object sender, EventArgs args) {
                ++clicks;
                var value = editor.Text;
                if (value.Length > 0)
                {
                    File.AppendAllText(Path.Combine(root,"sent.txt"), value + "\n",
                                      new UTF8Encoding(false));
                    posted.Text = value;
                    editor.Clear();
                    send.Enabled = false;  // Mirrors a delivered, cleared composer.
                }
            };
            Controls.Add(send);
        }
        Shown += delegate(object sender, EventArgs args) {
            Activate();
            BringToFront();
            editor.Focus();
            File.WriteAllText(Path.Combine(root,"ready.txt"), "READY");
        };
        FormClosed += delegate(object sender, FormClosedEventArgs args) {
            File.WriteAllText(Path.Combine(root,"final-editor.txt"),
                              editor.Text, new UTF8Encoding(false));
            File.WriteAllText(Path.Combine(root,"clicks.txt"),clicks.ToString());
        };
    }

    [STAThread]
    private static int Main(string[] args)
    {
        if (args.Length != 4) return 2;
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        Application.Run(new UniversalCourierFixture(
            args[0],args[1],args[2],args[3] == "send"));
        return 0;
    }
}
